"""Film Notebook endpoints (plan §3.8, Faz 7B). Sign-in required; own data only."""

from __future__ import annotations

import json
import logging

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.params import get_language, get_page
from apps.catalog.tmdb_client import TMDBClient, TMDBError, TMDBNotFoundError
from apps.notebook.models import NotebookEntry
from apps.notebook.serializers import (
    LookupSerializer,
    MergeSerializer,
    NotebookEntrySerializer,
    NotebookQuerySerializer,
    NotebookWriteSerializer,
)
from apps.notebook.services import (
    export_csv,
    export_rows,
    lookup,
    merge_guest_favorites,
    stats,
    upsert_entry,
)

logger = logging.getLogger(__name__)
PAGE_SIZE = 30


def _error(code: str, message: str, http_status: int) -> Response:
    return Response(
        {
            "error": {
                "code": code,
                "message": message,
                "status_code": http_status,
                "details": None,
            }
        },
        status=http_status,
    )


def _tmdb() -> TMDBClient | None:
    try:
        return TMDBClient()
    except ValueError:  # TMDB_API_KEY missing
        return None


class NotebookListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="My notebook (filter, search, sort, paginate)",
        parameters=[NotebookQuerySerializer, OpenApiParameter("page", int, default=1)],
        responses={200: NotebookEntrySerializer(many=True)},
        tags=["Notebook"],
    )
    def get(self, request):
        query = NotebookQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        f = query.validated_data
        entries = NotebookEntry.objects.filter(user=request.user)
        if "status" in f:
            entries = entries.filter(status=f["status"])
        if f["favorites"]:
            entries = entries.filter(is_favorite=True)
        if "media_type" in f:
            entries = entries.filter(media_type=f["media_type"])
        if "rating_min" in f:
            entries = entries.filter(rating_x2__gte=f["rating_min"])
        if "rating_max" in f:
            entries = entries.filter(rating_x2__lte=f["rating_max"])
        if "q" in f:
            entries = entries.filter(
                Q(title__icontains=f["q"])
                | Q(original_title__icontains=f["q"])
                | Q(note__icontains=f["q"])
            )
        if "tag" in f or "genre" in f:
            # JSON list membership; filtered in Python to stay portable across databases.
            entries = [
                e
                for e in entries
                if ("tag" not in f or f["tag"] in e.tags)
                and ("genre" not in f or f["genre"] in e.genres)
            ]
            items = sorted(
                entries, key=_sort_key(f["sort"]), reverse=f["sort"].startswith("-")
            )
        else:
            items = list(
                entries.order_by(NotebookQuerySerializer.SORTS[f["sort"]], "-id")
            )
        page = get_page(request)
        start = (page - 1) * PAGE_SIZE
        return Response(
            {
                "page": page,
                "total_results": len(items),
                "total_pages": max((len(items) + PAGE_SIZE - 1) // PAGE_SIZE, 1),
                "results": NotebookEntrySerializer(
                    items[start : start + PAGE_SIZE], many=True
                ).data,
            }
        )


def _sort_key(sort: str):
    field = NotebookQuerySerializer.SORTS[sort].lstrip("-")

    def key(entry):
        value = getattr(entry, field)
        return (
            (value is not None, value or 0)
            if field != "title"
            else (entry.title or "").lower()
        )

    return key


class NotebookEntryView(APIView):
    permission_classes = [IsAuthenticated]

    def _entry(self, request, media_type: str, tmdb_id: int) -> NotebookEntry:
        # Only the owner's rows are ever looked up: others' entries are simply 404.
        return get_object_or_404(
            NotebookEntry, user=request.user, media_type=media_type, tmdb_id=tmdb_id
        )

    @extend_schema(
        summary="One notebook entry",
        responses={200: NotebookEntrySerializer},
        tags=["Notebook"],
    )
    def get(self, request, media_type: str, tmdb_id: int):
        return Response(
            NotebookEntrySerializer(self._entry(request, media_type, tmdb_id)).data
        )

    @extend_schema(
        summary="Create or update an entry (status, rating, note, …)",
        request=NotebookWriteSerializer,
        responses={200: NotebookEntrySerializer, 201: NotebookEntrySerializer},
        tags=["Notebook"],
    )
    def put(self, request, media_type: str, tmdb_id: int):
        return self._write(request, media_type, tmdb_id)

    @extend_schema(
        summary="Partially update an entry (created if missing)",
        request=NotebookWriteSerializer,
        responses={200: NotebookEntrySerializer, 201: NotebookEntrySerializer},
        tags=["Notebook"],
    )
    def patch(self, request, media_type: str, tmdb_id: int):
        return self._write(request, media_type, tmdb_id)

    def _write(self, request, media_type: str, tmdb_id: int):
        if media_type not in ("movie", "tv"):
            return _error(
                "invalid_media_type", "media_type must be 'movie' or 'tv'.", 400
            )
        serializer = NotebookWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            entry, created = upsert_entry(
                request.user,
                media_type,
                tmdb_id,
                serializer.validated_data,
                client=_tmdb(),
                language=get_language(request),
            )
        except TMDBNotFoundError:
            return _error("title_not_found", "Title not found on TMDB.", 404)
        except TMDBError as exc:
            logger.error("Notebook snapshot failed: %s", exc)
            return _error(
                "service_unavailable", "The movie database (TMDB) is unavailable.", 503
            )
        return Response(
            NotebookEntrySerializer(entry).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Remove a title from my notebook",
        responses={204: None},
        tags=["Notebook"],
    )
    def delete(self, request, media_type: str, tmdb_id: int):
        self._entry(request, media_type, tmdb_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotebookLookupView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="My state for many titles at once (result cards)",
        request=LookupSerializer,
        tags=["Notebook"],
    )
    def post(self, request):
        serializer = LookupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        keys = [
            (i["media_type"], i["tmdb_id"]) for i in serializer.validated_data["items"]
        ]
        return Response(lookup(request.user, keys))


class NotebookStatsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="My notebook statistics", tags=["Notebook"])
    def get(self, request):
        return Response(stats(request.user))


class NotebookExportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Export my notebook (CSV or JSON)",
        parameters=[
            OpenApiParameter("format", str, enum=["csv", "json"], default="csv")
        ],
        tags=["Notebook"],
    )
    def get(self, request):
        fmt = request.query_params.get("format", "csv")
        if fmt == "json":
            body = json.dumps(export_rows(request.user), ensure_ascii=False, indent=2)
            response = HttpResponse(
                body, content_type="application/json; charset=utf-8"
            )
            response["Content-Disposition"] = (
                'attachment; filename="cineglobe-notebook.json"'
            )
            return response
        if fmt != "csv":
            return _error("invalid_format", "format must be csv or json.", 400)
        # BOM so Excel opens Turkish characters correctly.
        response = HttpResponse(
            "﻿" + export_csv(request.user), content_type="text/csv; charset=utf-8"
        )
        response["Content-Disposition"] = (
            'attachment; filename="cineglobe-notebook.csv"'
        )
        return response

    # DRF reserves ?format= for picking a renderer and would 404 on "csv"; this
    # view builds its own response, so fall back to the default renderer instead.
    def perform_content_negotiation(self, request, force=False):
        return super().perform_content_negotiation(request, force=True)


class NotebookMergeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Bring browser-only favourites into my account (account data wins)",
        request=MergeSerializer,
        tags=["Notebook"],
    )
    def post(self, request):
        serializer = MergeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        items = [
            (i["media_type"], i["tmdb_id"])
            for i in serializer.validated_data["favorites"]
        ]
        result = merge_guest_favorites(
            request.user, items, _tmdb(), get_language(request)
        )
        return Response(result)
