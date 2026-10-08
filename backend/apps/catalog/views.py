"""Catalog API views: title detail with multi-language support."""

import logging

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Title
from apps.catalog.params import get_language
from apps.catalog.serializers import TitleSerializer
from apps.catalog.tmdb_client import (
    TMDBClient,
    TMDBError,
    TMDBNotFoundError,
    normalize_language,
)

logger = logging.getLogger(__name__)


def _fetch_and_cache_title(
    media_type: str, tmdb_id: int, language: str = "tr-TR"
) -> Title:
    """Fetch a Title from TMDB, persist/update in DB, and return the instance."""
    try:
        client = TMDBClient()
    except ValueError as exc:  # TMDB_API_KEY missing: answer 503, not 500
        raise TMDBError(str(exc)) from exc
    normalized_lang = normalize_language(language)

    if media_type == Title.MOVIE:
        data = client.get_movie_detail(tmdb_id, language=normalized_lang)
    else:
        data = client.get_tv_detail(tmdb_id, language=normalized_lang)

    fetched_title = data.get("title") or data.get("name", "")
    fetched_overview = data.get("overview", "")

    common = {
        "original_title": data.get("original_title") or data.get("original_name", ""),
        "poster_path": data.get("poster_path", "") or "",
        "backdrop_path": data.get("backdrop_path", "") or "",
        "original_language": data.get("original_language", ""),
        "vote_average": data.get("vote_average", 0.0),
        "vote_count": data.get("vote_count", 0),
        "popularity": data.get("popularity", 0.0),
        "release_date": data.get("release_date") or None,
        "first_air_date": data.get("first_air_date") or None,
    }

    if normalized_lang.startswith("en"):
        common["title_en"] = fetched_title
        common["overview_en"] = fetched_overview
    else:
        common["title"] = fetched_title
        common["overview"] = fetched_overview

    title_obj, _ = Title.objects.update_or_create(
        media_type=media_type,
        tmdb_id=tmdb_id,
        defaults=common,
    )
    return title_obj


class TitleDetailView(APIView):
    """Retrieve a single movie or TV show by TMDB ID."""

    @extend_schema(
        summary="Retrieve a movie or TV show detail",
        parameters=[
            OpenApiParameter(
                "media_type",
                location=OpenApiParameter.PATH,
                description="Either 'movie' or 'tv'",
                enum=["movie", "tv"],
            ),
            OpenApiParameter(
                "tmdb_id",
                location=OpenApiParameter.PATH,
                description="TMDB numeric ID of the title",
                type=int,
            ),
            OpenApiParameter(
                "lang",
                location=OpenApiParameter.QUERY,
                description="Language preference: 'tr' or 'en'",
                type=str,
                default="tr",
            ),
        ],
        responses={
            200: TitleSerializer,
            400: OpenApiResponse(description="Invalid media_type parameter"),
            404: OpenApiResponse(description="Title not found on TMDB"),
            503: OpenApiResponse(description="TMDB is currently unavailable"),
        },
        tags=["Catalog"],
    )
    def get(self, request, media_type: str, tmdb_id: int):
        if media_type not in (Title.MOVIE, Title.TV):
            return Response(
                {
                    "error": {
                        "code": "invalid_media_type",
                        "message": "media_type must be 'movie' or 'tv'.",
                        "status_code": 400,
                        "details": None,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        lang = get_language(request)

        try:
            title = _fetch_and_cache_title(media_type, tmdb_id, language=lang)
        except TMDBNotFoundError:
            return Response(
                {
                    "error": {
                        "code": "not_found",
                        "message": f"TMDB {media_type} with id {tmdb_id} was not found.",
                        "status_code": 404,
                        "details": None,
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except TMDBError as exc:
            # Outage, rate limit, rejected/missing API key: none is the client's fault.
            logger.error("TMDB unavailable: %s", exc)
            return Response(
                {
                    "error": {
                        "code": "service_unavailable",
                        "message": (
                            "Film veritabanı (TMDB) şu anda erişilemiyor. Lütfen kısa süre sonra tekrar deneyin."
                            if not lang.lower().startswith("en")
                            else "Movie database (TMDB) is currently unavailable. Please try again shortly."
                        ),
                        "status_code": 503,
                        "details": None,
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer = TitleSerializer(title, context={"language": lang})
        return Response(serializer.data)
