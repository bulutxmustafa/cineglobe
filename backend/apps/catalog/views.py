"""Catalog API views: Title detail, Curated Categories, and Upcoming releases with multi-language support."""

import logging
from datetime import date, datetime
from typing import Any

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.categories import get_all_curated_categories, get_curated_category
from apps.catalog.formatting import format_tmdb_item
from apps.catalog.models import Title
from apps.catalog.params import get_language, get_page
from apps.catalog.serializers import TitleSerializer
from apps.catalog.tmdb_client import (
    TMDBClient,
    TMDBNotFoundError,
    TMDBServiceUnavailableError,
    normalize_language,
)

logger = logging.getLogger(__name__)


def _fetch_and_cache_title(
    media_type: str, tmdb_id: int, language: str = "tr-TR"
) -> Title:
    """Fetch a Title from TMDB, persist/update in DB, and return the instance."""
    client = TMDBClient()
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
        except TMDBServiceUnavailableError as exc:
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


class CuratedCategoryListView(APIView):
    """List all curated and mood-based categories."""

    @extend_schema(
        summary="List all curated / mood categories",
        parameters=[
            OpenApiParameter(
                "lang",
                location=OpenApiParameter.QUERY,
                description="Language: 'tr' or 'en'",
            ),
        ],
        tags=["Categories"],
    )
    def get(self, request):
        lang = get_language(request)
        categories = get_all_curated_categories(language=lang)
        return Response({"categories": categories, "count": len(categories)})


class CuratedCategoryDetailView(APIView):
    """Get titles belonging to a specific curated mood category."""

    @extend_schema(
        summary="Get titles for a curated category",
        parameters=[
            OpenApiParameter(
                "slug", location=OpenApiParameter.PATH, description="Category slug"
            ),
            OpenApiParameter(
                "page", location=OpenApiParameter.QUERY, type=int, default=1
            ),
            OpenApiParameter(
                "lang",
                location=OpenApiParameter.QUERY,
                description="Language: 'tr' or 'en'",
            ),
        ],
        tags=["Categories"],
    )
    def get(self, request, slug: str):
        category = get_curated_category(slug)
        if not category:
            return Response(
                {
                    "error": {
                        "code": "category_not_found",
                        "message": f"Kategori '{slug}' bulunamadı.",
                        "status_code": 404,
                        "details": None,
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        lang = get_language(request)
        page = get_page(request)
        client = TMDBClient()

        results: list[dict[str, Any]] = []

        try:
            if category.media_type in ("movie", "both") and category.tmdb_params_movie:
                movie_params = {"page": page, **category.tmdb_params_movie}
                movie_res = client.discover_movies(movie_params, language=lang)
                for item in movie_res.get("results", []):
                    results.append(format_tmdb_item(item, default_media_type="movie"))

            if category.media_type in ("tv", "both") and category.tmdb_params_tv:
                tv_params = {"page": page, **category.tmdb_params_tv}
                tv_res = client.discover_tv(tv_params, language=lang)
                for item in tv_res.get("results", []):
                    results.append(format_tmdb_item(item, default_media_type="tv"))

        except TMDBServiceUnavailableError as exc:
            logger.error("TMDB error in category fetch: %s", exc)
            return Response(
                {
                    "error": {
                        "code": "service_unavailable",
                        "message": "Film veritabanı geçici olarak erişilemiyor.",
                        "status_code": 503,
                        "details": None,
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Sort combined results by popularity or vote average
        results.sort(
            key=lambda x: (x.get("vote_average", 0), x.get("popularity", 0)),
            reverse=True,
        )

        return Response(
            {
                "category": category.to_dict(language=lang),
                "page": page,
                "count": len(results),
                "results": results,
            }
        )


class UpcomingTitlesView(APIView):
    """List upcoming film and TV releases with release countdown and reminder support."""

    @extend_schema(
        summary="List upcoming movies and series",
        parameters=[
            OpenApiParameter(
                "media_type",
                location=OpenApiParameter.QUERY,
                enum=["both", "movie", "tv"],
                default="both",
            ),
            OpenApiParameter(
                "page", location=OpenApiParameter.QUERY, type=int, default=1
            ),
            OpenApiParameter(
                "lang",
                location=OpenApiParameter.QUERY,
                description="Language: 'tr' or 'en'",
            ),
        ],
        tags=["Upcoming"],
    )
    def get(self, request):
        media_type = request.query_params.get("media_type", "both")
        lang = get_language(request)
        page = get_page(request)
        client = TMDBClient()
        today = date.today()

        items: list[dict[str, Any]] = []

        try:
            if media_type in ("movie", "both"):
                movie_data = client.get_upcoming_movies(page=page, language=lang)
                for m in movie_data.get("results", []):
                    formatted = format_tmdb_item(m, default_media_type="movie")
                    items.append(self._enrich_upcoming(formatted, today))

            if media_type in ("tv", "both"):
                tv_data = client.get_upcoming_tv(page=page, language=lang)
                for t in tv_data.get("results", []):
                    formatted = format_tmdb_item(t, default_media_type="tv")
                    items.append(self._enrich_upcoming(formatted, today))

        except TMDBServiceUnavailableError as exc:
            logger.error("TMDB error in upcoming fetch: %s", exc)
            return Response(
                {
                    "error": {
                        "code": "service_unavailable",
                        "message": "Yaklaşan yapımlar verisi şu an alınamıyor.",
                        "status_code": 503,
                        "details": None,
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Sort by release date ascending (soonest first)
        items.sort(
            key=lambda x: (
                x.get("countdown_days") if x.get("countdown_days") is not None else 9999
            )
        )

        return Response(
            {
                "page": page,
                "media_type": media_type,
                "count": len(items),
                "results": items,
            }
        )

    def _enrich_upcoming(self, item: dict[str, Any], today: date) -> dict[str, Any]:
        """Calculate countdown days and attach reminder readiness flag."""
        rel_str = item.get("release_date", "")
        countdown_days = None
        is_upcoming = True

        if rel_str:
            try:
                rel_date = datetime.strptime(rel_str, "%Y-%m-%d").date()
                delta = (rel_date - today).days
                countdown_days = max(0, delta)
                is_upcoming = delta >= 0
            except ValueError:
                pass

        item["countdown_days"] = countdown_days
        item["is_unreleased"] = is_upcoming
        item["can_set_reminder"] = is_upcoming
        return item
