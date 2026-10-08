"""Natural-language search endpoint: POST /api/v1/search/."""

import logging
import re

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import (
    AnonRateThrottle,
    ScopedRateThrottle,
    UserRateThrottle,
)
from rest_framework.views import APIView

from apps.catalog.params import get_language
from apps.catalog.tmdb_client import TMDBError
from apps.search.serializers import SearchRequestSerializer, SearchResponseSerializer
from apps.search.service import QueryNotUnderstoodError, SearchService

logger = logging.getLogger(__name__)

HAS_LETTER = re.compile(r"[^\W\d_]")

MESSAGES = {
    "invalid_query": {
        "tr": "Ne izlemek istediğini anlayamadım. Tür, tema veya ruh hali yazmayı dene; "
        "örn. 'gerilim olsun ama korku içermesin' ya da 'kısa bölümlü komik bir dizi'.",
        "en": "I couldn't tell what you'd like to watch. Try a genre, theme or mood, "
        "e.g. 'a thriller but no horror' or 'a funny series with short episodes'.",
    },
    "service_unavailable": {
        "tr": "Film veritabanı (TMDB) şu anda erişilemiyor. Lütfen kısa süre sonra tekrar deneyin.",
        "en": "The movie database (TMDB) is currently unavailable. Please try again shortly.",
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


class SearchView(APIView):
    """Find movies and series from a free-text request, with a reason for each."""

    throttle_classes = [AnonRateThrottle, UserRateThrottle, ScopedRateThrottle]
    throttle_scope = "search"

    @extend_schema(
        summary="Natural-language movie & TV search",
        request=SearchRequestSerializer,
        responses={
            200: SearchResponseSerializer,
            400: OpenApiResponse(description="Empty or meaningless query"),
            429: OpenApiResponse(description="Rate limit exceeded"),
            503: OpenApiResponse(description="TMDB is currently unavailable"),
        },
        tags=["Search"],
    )
    def post(self, request):
        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        language = data.get("lang") or get_language(request)
        query = data["query"]

        if len(query) < 2 or not HAS_LETTER.search(query):
            return _error("invalid_query", language, status.HTTP_400_BAD_REQUEST)

        try:
            payload = SearchService().search(query, data["media_type"], language)
        except QueryNotUnderstoodError:
            return _error("invalid_query", language, status.HTTP_400_BAD_REQUEST)
        except TMDBError as exc:
            logger.error("Search failed due to TMDB: %s", exc)
            return _error(
                "service_unavailable", language, status.HTTP_503_SERVICE_UNAVAILABLE
            )

        return Response(payload)
