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

# TMDB genres: News, Reality, Soap, Talk.
NOT_CINEMATIC = {10763, 10764, 10766, 10767}


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

    from apps.catalog.backdrops import choose_backdrop

    poster_path = data.get("poster_path", "") or ""
    backdrop_path = choose_backdrop(
        client, media_type, tmdb_id, poster_path, data.get("backdrop_path", "") or ""
    )
    common = {
        "original_title": data.get("original_title") or data.get("original_name", ""),
        "poster_path": poster_path,
        "backdrop_path": backdrop_path,
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


def rank_trailers(videos: list[dict]) -> list[dict]:
    """YouTube trailers and teasers, best first: official trailers, then any
    trailer, then teasers."""

    def rank(v: dict) -> tuple:
        kind = {"Trailer": 0, "Teaser": 1}.get(v.get("type", ""), 9)
        return (kind, not v.get("official", False), v.get("published_at") or "")

    usable = [
        v
        for v in videos
        if v.get("site") == "YouTube"
        and v.get("key")
        and v.get("type") in ("Trailer", "Teaser")
    ]
    return sorted(usable, key=rank)


def pick_trailer(videos: list[dict]) -> dict | None:
    """Best YouTube trailer, without checking whether it still plays."""
    ranked = rank_trailers(videos)
    return ranked[0] if ranked else None


def youtube_playable(key: str) -> bool:
    """Whether a YouTube video still exists and may be embedded (oEmbed check).

    TMDB keeps links to videos that were later deleted or made private. A network
    problem counts as playable so a slow YouTube never hides every trailer."""
    import httpx
    from django.core.cache import cache

    cache_key = f"yt:playable:{key}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        response = httpx.get(
            "https://www.youtube.com/oembed",
            params={"url": f"https://www.youtube.com/watch?v={key}", "format": "json"},
            timeout=3,
        )
    except httpx.HTTPError:
        return True
    playable = response.status_code == 200
    if response.status_code in (200, 401, 403, 404):
        cache.set(cache_key, playable, 86400)
    return playable


TRAILER_MAX_CHECKS = 6


class TitleTrailerView(APIView):
    """GET /api/v1/titles/{media_type}/{tmdb_id}/trailer/: a YouTube trailer, if any.

    The site language is tried first; when there is no trailer in it, English."""

    authentication_classes: list = []

    @extend_schema(
        summary="YouTube trailer of a movie or series",
        parameters=[OpenApiParameter("lang", str, enum=["tr", "en"], default="tr")],
        tags=["Catalog"],
    )
    def get(self, request, media_type: str, tmdb_id: int):
        from apps.catalog.http import cdn_cache

        if media_type not in ("movie", "tv"):
            return Response(
                {
                    "error": {
                        "code": "invalid",
                        "message": "media_type must be movie or tv.",
                        "status_code": 400,
                        "details": None,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        language = normalize_language(get_language(request))
        client = TMDBClient()
        candidates: list[dict] = []
        try:
            for lang in dict.fromkeys([language, "en-US"]):
                videos = client.get_videos(media_type, tmdb_id, language=lang)
                candidates += rank_trailers(videos.get("results", []))
        except TMDBNotFoundError:
            candidates = []
        except TMDBError as exc:
            logger.warning("Trailer unavailable: %s", exc)
            return Response(
                {
                    "error": {
                        "code": "service_unavailable",
                        "message": "TMDB is unavailable.",
                        "status_code": 503,
                        "details": None,
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        # The first few candidates that still play on YouTube (deleted videos skipped).
        seen: set[str] = set()
        trailer = None
        for video in candidates:
            if video["key"] in seen or len(seen) >= TRAILER_MAX_CHECKS:
                continue
            seen.add(video["key"])
            if youtube_playable(video["key"]):
                trailer = video
                break
        body = {"trailer": None}
        if trailer:
            body["trailer"] = {
                "key": trailer["key"],
                "name": trailer.get("name", ""),
                "language": trailer.get("iso_639_1", ""),
                "type": trailer.get("type", ""),
            }
        return cdn_cache(Response(body), request, 86400)


class GuideListView(APIView):
    """GET /api/v1/guides/: the search-friendly film and series guides."""

    authentication_classes: list = []

    @extend_schema(
        summary="List film and series guides",
        parameters=[OpenApiParameter("lang", str, enum=["tr", "en"], default="tr")],
        tags=["Catalog"],
    )
    def get(self, request):
        from apps.catalog.guides import GUIDES
        from apps.catalog.http import cdn_cache

        lang = normalize_language(get_language(request))
        body = {
            "guides": [
                {
                    "slug": g.slug,
                    "media_type": g.media_type,
                    "title": g.title(lang),
                    "intro": g.intro(lang),
                }
                for g in GUIDES
            ]
        }
        return cdn_cache(Response(body), request, 86400)


class GuideDetailView(APIView):
    """GET /api/v1/guides/{slug}/: one guide with its ranked titles."""

    authentication_classes: list = []

    @extend_schema(
        summary="One film or series guide with its titles",
        parameters=[OpenApiParameter("lang", str, enum=["tr", "en"], default="tr")],
        tags=["Catalog"],
    )
    def get(self, request, slug: str):
        from apps.catalog.formatting import format_tmdb_item
        from apps.catalog.guides import GUIDES_BY_SLUG
        from apps.catalog.http import cdn_cache

        guide = GUIDES_BY_SLUG.get(slug)
        if guide is None:
            return Response(
                {
                    "error": {
                        "code": "not_found",
                        "message": "Guide not found.",
                        "status_code": 404,
                        "details": None,
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        lang = normalize_language(get_language(request))
        try:
            client = TMDBClient()
            discover = (
                client.discover_movies
                if guide.media_type == "movie"
                else client.discover_tv
            )
            items: list[dict] = []
            for page in (1, 2):
                data = discover(
                    {**guide.discover_params(), "page": page}, language=lang
                )
                items += [
                    format_tmdb_item(i, guide.media_type)
                    for i in data.get("results", [])
                ]
        except (TMDBError, ValueError) as exc:
            logger.warning("Guide %s unavailable: %s", slug, exc)
            return Response(
                {
                    "error": {
                        "code": "service_unavailable",
                        "message": "TMDB is unavailable.",
                        "status_code": 503,
                        "details": None,
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        results = [
            i
            for i in items
            if i["poster_url"] and not NOT_CINEMATIC.intersection(i["genre_ids"])
        ][:30]
        body = {
            "guide": {
                "slug": guide.slug,
                "media_type": guide.media_type,
                "title": guide.title(lang),
                "intro": guide.intro(lang),
            },
            "results": results,
        }
        return cdn_cache(Response(body), request, 21600)


# Titles always on the home wall (TV: The Mentalist), plus filters for the rest.
WALL_PINS: list[tuple[str, int]] = [("tv", 5920)]
WALL_MIN_VOTES = 150
WALL_MAX = 90


class PopularView(APIView):
    """GET /api/v1/popular/: what people watch most right now (home page wall)."""

    # Public and anonymous: no `Vary: Cookie`, so the CDN can share the response.
    authentication_classes: list = []

    @extend_schema(
        summary="Currently popular movies and series",
        parameters=[
            OpenApiParameter(
                "media_type", str, enum=["both", "movie", "tv"], default="both"
            ),
            OpenApiParameter("lang", str, enum=["tr", "en"], default="tr"),
        ],
        tags=["Catalog"],
    )
    def get(self, request):
        from apps.catalog.formatting import format_tmdb_item
        from apps.catalog.http import cdn_cache

        media_type = request.query_params.get("media_type", "both")
        if media_type not in ("both", "movie", "tv"):
            return Response(
                {
                    "error": {
                        "code": "invalid",
                        "message": "media_type must be both, movie or tv.",
                        "status_code": 400,
                        "details": None,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        language = normalize_language(get_language(request))
        try:
            client = TMDBClient()
            raw: list[dict] = []
            # What people watch most this week, then the classic popular lists.
            for page in (1, 2):
                for i in client.get_trending(page=page, language=language).get(
                    "results", []
                ):
                    if i.get("media_type") in ("movie", "tv"):
                        raw.append(format_tmdb_item(i, i["media_type"]))
            for page in (1, 2):
                if media_type in ("both", "movie"):
                    data = client.get_popular_movies(page=page, language=language)
                    raw += [
                        format_tmdb_item(i, "movie") for i in data.get("results", [])
                    ]
                if media_type in ("both", "tv"):
                    data = client.get_popular_tv(page=page, language=language)
                    raw += [format_tmdb_item(i, "tv") for i in data.get("results", [])]
            pins = []
            for pin_type, pin_id in WALL_PINS:
                if media_type not in ("both", pin_type):
                    continue
                try:
                    detail = (
                        client.get_tv_detail(pin_id, language=language)
                        if pin_type == "tv"
                        else client.get_movie_detail(pin_id, language=language)
                    )
                    pins.append(format_tmdb_item(detail, pin_type))
                except (TMDBError, ValueError):
                    continue
        except (TMDBError, ValueError) as exc:
            logger.warning("Popular titles unavailable: %s", exc)
            return Response(
                {
                    "error": {
                        "code": "service_unavailable",
                        "message": "TMDB is unavailable.",
                        "status_code": 503,
                        "details": None,
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        # Only well-known, cinematic titles: no talk/news/reality/soap shows and
        # nothing too obscure (few votes), so the wall shows what people really watch.
        seen: set[tuple[str, int]] = set()
        items: list[dict] = []
        for i in pins + sorted(raw, key=lambda i: i["popularity"], reverse=True):
            key = (i["media_type"], i["tmdb_id"])
            if key in seen or not i["poster_url"]:
                continue
            if i not in pins and (
                media_type not in ("both", i["media_type"])
                or NOT_CINEMATIC.intersection(i["genre_ids"])
                or (i.get("vote_count") or 0) < WALL_MIN_VOTES
            ):
                continue
            seen.add(key)
            items.append(i)
        items = items[:WALL_MAX]
        return cdn_cache(
            Response({"count": len(items), "results": items}), request, 3600
        )
