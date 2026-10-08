"""Reminder endpoints (plan §3.7, Faz 7) and the daily cron trigger."""

from __future__ import annotations

import hmac
import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.params import get_language
from apps.catalog.tmdb_client import TMDBClient, TMDBError
from apps.reminders.jobs import run_daily
from apps.reminders.models import Reminder
from apps.reminders.serializers import (
    ReminderBulkSerializer,
    ReminderCreateSerializer,
    ReminderSerializer,
)
from apps.reminders.services import ReminderError, cancel_reminder, create_reminder

logger = logging.getLogger(__name__)

MESSAGES = {
    "already_released": {
        "tr": "Bu yapım zaten çıktı; hatırlatıcı kurulamaz.",
        "en": "This title is already out, so no reminder can be set.",
    },
    "no_upcoming_season": {
        "tr": "Bu dizi için duyurulmuş yeni bir sezon yok.",
        "en": "No new season has been announced for this series.",
    },
    "title_not_found": {"tr": "Yapım bulunamadı.", "en": "Title not found."},
    "service_unavailable": {
        "tr": "Film veritabanı (TMDB) şu anda erişilemiyor.",
        "en": "The movie database (TMDB) is currently unavailable.",
    },
}


def _error(code: str, language: str, http_status: int) -> Response:
    return Response(
        {
            "error": {
                "code": code,
                "message": MESSAGES[code][language],
                "status_code": http_status,
                "details": None,
            }
        },
        status=http_status,
    )


def _tmdb() -> TMDBClient:
    try:
        return TMDBClient()
    except ValueError as exc:
        raise TMDBError(str(exc)) from exc


class RemindersView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="My reminders",
        responses={200: ReminderSerializer(many=True)},
        tags=["Reminders"],
    )
    def get(self, request):
        reminders = Reminder.objects.filter(user=request.user).exclude(
            status=Reminder.Status.CANCELLED
        )
        data = [
            {**ReminderSerializer(r).data, "due_date": r.due_date()} for r in reminders
        ]
        return Response(data)

    @extend_schema(
        summary="Remind me when a title comes out (one per title)",
        request=ReminderCreateSerializer,
        responses={
            201: ReminderSerializer,
            200: ReminderSerializer,
            400: OpenApiResponse(description="already_released / no_upcoming_season"),
        },
        tags=["Reminders"],
    )
    def post(self, request):
        serializer = ReminderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        language = get_language(request)
        try:
            reminder, created = create_reminder(
                request.user,
                language=language,
                client=_tmdb(),
                **serializer.validated_data,
            )
        except ReminderError as exc:
            http = (
                status.HTTP_404_NOT_FOUND
                if exc.code == "title_not_found"
                else status.HTTP_400_BAD_REQUEST
            )
            return _error(exc.code, language, http)
        except TMDBError as exc:
            logger.error("Reminder TMDB failure: %s", exc)
            return _error(
                "service_unavailable", language, status.HTTP_503_SERVICE_UNAVAILABLE
            )
        body = {**ReminderSerializer(reminder).data, "due_date": reminder.due_date()}
        return Response(
            body, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class ReminderBulkView(APIView):
    """After sign-in the web app sends the guest's pending 'Remind me' clicks here."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create several reminders (guest → account hand-over)",
        request=ReminderBulkSerializer,
        tags=["Reminders"],
    )
    def post(self, request):
        serializer = ReminderBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        language = get_language(request)
        client = _tmdb()
        created, skipped = [], []
        for item in serializer.validated_data["items"]:
            try:
                reminder, _ = create_reminder(
                    request.user, language=language, client=client, **item
                )
                created.append(ReminderSerializer(reminder).data)
            except (ReminderError, TMDBError) as exc:
                code = (
                    exc.code
                    if isinstance(exc, ReminderError)
                    else "service_unavailable"
                )
                skipped.append(
                    {
                        "media_type": item["media_type"],
                        "tmdb_id": item["tmdb_id"],
                        "code": code,
                    }
                )
        return Response({"created": created, "skipped": skipped})


class ReminderItemView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Cancel a reminder", responses={204: None}, tags=["Reminders"]
    )
    def delete(self, request, pk: int):
        # Another user's reminder is a 404, so its existence is not revealed.
        cancel_reminder(get_object_or_404(Reminder, pk=pk, user=request.user))
        return Response(status=status.HTTP_204_NO_CONTENT)


class DailyCronView(APIView):
    """Vercel Cron calls this once a day with `Authorization: Bearer <CRON_SECRET>`."""

    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_classes: list = []

    @extend_schema(summary="Run the daily job (cron only)", tags=["Ops"])
    def get(self, request):
        secret = settings.CRON_SECRET
        supplied = request.headers.get("Authorization", "")
        if not secret or not hmac.compare_digest(supplied, f"Bearer {secret}"):
            # 404 rather than 401: do not advertise the endpoint.
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(run_daily().as_dict())
