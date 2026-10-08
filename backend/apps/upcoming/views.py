"""GET /api/v1/upcoming/ (plan §3.7, Faz 4C)."""

from __future__ import annotations

import logging

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.http import cdn_cache
from apps.catalog.params import get_language, get_page
from apps.catalog.tmdb_client import TMDBClient, TMDBError
from apps.upcoming.serializers import (
    UpcomingQuerySerializer,
    UpcomingResponseSerializer,
)
from apps.upcoming.service import UpcomingService

logger = logging.getLogger(__name__)

# Release dates move; keep the CDN copy short (plan §3.7: 3–6 hours overall).
CDN_SECONDS = 1800
UNAVAILABLE = {
    "tr": "Film veritabanı (TMDB) şu anda erişilemiyor. Lütfen kısa süre sonra tekrar deneyin.",
    "en": "The movie database (TMDB) is currently unavailable. Please try again shortly.",
}


def _tmdb() -> TMDBClient:
    try:
        return TMDBClient()
    except ValueError as exc:  # TMDB_API_KEY missing: a server problem, not a 500
        raise TMDBError(str(exc)) from exc


class UpcomingView(APIView):
    # Public and anonymous: no session access, so no `Vary: Cookie` for the CDN.
    authentication_classes: list = []

    @extend_schema(
        summary="Upcoming movies and series, grouped by release date",
        description=(
            "Only titles released today or later (Europe/Istanbul). Movies use the "
            "Turkish release date when one exists, otherwise the global date. Groups: "
            "this_week, this_month, later, tba (date not announced)."
        ),
        parameters=[
            UpcomingQuerySerializer,
            OpenApiParameter("page", int, default=1),
            OpenApiParameter("lang", str, enum=["tr", "en"], default="tr"),
        ],
        responses={200: UpcomingResponseSerializer},
        tags=["Upcoming"],
    )
    def get(self, request):
        query = UpcomingQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        language = get_language(request)
        page = get_page(request)
        try:
            payload = UpcomingService(_tmdb()).page(
                language=language, page=page, **query.validated_data
            )
        except TMDBError as exc:
            logger.error("Upcoming failed: %s", exc)
            return Response(
                {
                    "error": {
                        "code": "service_unavailable",
                        "message": UNAVAILABLE[language],
                        "status_code": 503,
                        "details": None,
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return cdn_cache(Response(payload), request, CDN_SECONDS)
