"""Natural-language search endpoint: POST /api/v1/search/."""

import logging
import re

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import (
    AnonRateThrottle,
    BaseThrottle,
    ScopedRateThrottle,
    UserRateThrottle,
)
from rest_framework.views import APIView

from apps.accounts.services import record_search
from apps.catalog.params import get_language
from apps.catalog.tmdb_client import TMDBError
from apps.search.cost_guard import quota_identity, quota_remaining
from apps.search.router import Quota
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


def _error(
    code: str, language: str, http_status: int, details: dict | None = None
) -> Response:
    return Response(
        {
            "error": {
                "code": code,
                "message": MESSAGES[code][language],
                "status_code": http_status,
                "details": details,
            }
        },
        status=http_status,
    )


def _quota_for(request) -> Quota:
    """Daily AI-search quota identity: the user if signed in, else the (hashed) IP."""
    user = request.user
    user_id = user.pk if user and user.is_authenticated else None
    # Same client identity DRF throttling uses: honours REST_FRAMEWORK["NUM_PROXIES"],
    # so behind Vercel's proxy each visitor gets their own quota (not one shared IP).
    identity, limit = quota_identity(user_id, BaseThrottle().get_ident(request))
    return Quota(identity, limit)


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

        quota = _quota_for(request)
        try:
            payload = SearchService().search(
                query, data["media_type"], language, quota=quota
            )
        except QueryNotUnderstoodError as exc:
            return _error(
                "invalid_query",
                language,
                status.HTTP_400_BAD_REQUEST,
                details={"ai_status": exc.ai_status},
            )
        except TMDBError as exc:
            logger.error("Search failed due to TMDB: %s", exc)
            return _error(
                "service_unavailable", language, status.HTTP_503_SERVICE_UNAVAILABLE
            )

        record_search(request.user, query, data["media_type"], language)
        signed_in = request.user.is_authenticated
        payload["quota"] = {
            "signed_in": signed_in,
            "limit": quota.limit,
            "remaining": quota_remaining(quota.identity, quota.limit),
            # Guests out of AI searches are invited to a free account (plan Faz 7).
            "suggest_signup": not signed_in
            and payload["ai_status"] == "quota_exceeded",
        }
        return Response(payload)
