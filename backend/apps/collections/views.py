"""Collection endpoints (plan §3.5, Faz 4B)."""

from __future__ import annotations

import logging
from functools import wraps

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.http import cdn_cache
from apps.catalog.params import get_language, get_page
from apps.catalog.tmdb_client import TMDBClient, TMDBError
from apps.collections.engine import PAGE_SIZE, RecipeEngine
from apps.collections.models import Collection
from apps.collections.serializers import (
    CollectionDetailResponseSerializer,
    CollectionListResponseSerializer,
    CollectionQuerySerializer,
    RandomPickResponseSerializer,
    RandomQuerySerializer,
)
from apps.notebook.services import watched_keys

logger = logging.getLogger(__name__)

CDN_SECONDS = 3600
# Anonymous and public: skipping auth keeps Django from touching the session,
# which would add `Vary: Cookie` and stop the CDN from sharing the response.
PUBLIC_AUTH: list = []
LANG_PARAM = OpenApiParameter("lang", str, enum=["tr", "en"], default="tr")
UNAVAILABLE = {
    "tr": "Film veritabanı (TMDB) şu anda erişilemiyor. Lütfen kısa süre sonra tekrar deneyin.",
    "en": "The movie database (TMDB) is currently unavailable. Please try again shortly.",
}


def _engine() -> RecipeEngine:
    try:
        return RecipeEngine(TMDBClient())
    except ValueError as exc:  # TMDB_API_KEY missing
        raise TMDBError(str(exc)) from exc


def tmdb_unavailable_as_503(view_method):
    @wraps(view_method)
    def wrapper(self, request, *args, **kwargs):
        try:
            return view_method(self, request, *args, **kwargs)
        except TMDBError as exc:
            logger.error("TMDB failure in %s: %s", type(self).__name__, exc)
            return Response(
                {
                    "error": {
                        "code": "service_unavailable",
                        "message": UNAVAILABLE[get_language(request)],
                        "status_code": 503,
                        "details": None,
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    return wrapper


class CollectionListView(APIView):
    authentication_classes = PUBLIC_AUTH

    @extend_schema(
        summary="List active curated collections",
        parameters=[LANG_PARAM],
        responses={200: CollectionListResponseSerializer},
        tags=["Collections"],
    )
    def get(self, request):
        language = get_language(request)
        collections = [
            c.summary(language) for c in Collection.objects.filter(is_active=True)
        ]
        response = Response({"count": len(collections), "collections": collections})
        return cdn_cache(response, request, CDN_SECONDS)


class CollectionDetailView(APIView):
    authentication_classes = PUBLIC_AUTH

    @extend_schema(
        summary="Titles of a curated collection (paginated)",
        parameters=[
            CollectionQuerySerializer,
            OpenApiParameter("page", int, default=1),
            LANG_PARAM,
        ],
        responses={200: CollectionDetailResponseSerializer},
        tags=["Collections"],
    )
    @tmdb_unavailable_as_503
    def get(self, request, slug: str):
        collection = get_object_or_404(Collection, slug=slug, is_active=True)
        query = CollectionQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        language = get_language(request)
        media_type = query.validated_data["media_type"]
        page = get_page(request)
        if query.validated_data["exclude_watched"]:
            return self._personal(request, collection, media_type, language, page)
        payload = _engine().page(collection, media_type, language, page)
        response = Response(
            {
                "collection": collection.summary(language),
                "media_type": media_type,
                **payload,
            }
        )
        return cdn_cache(response, request, CDN_SECONDS)

    @staticmethod
    def _personal(request, collection, media_type, language, page):
        """Same list minus the user's watched titles. Session is read explicitly
        (the view is otherwise auth-less for CDN sharing) and never CDN-cached."""
        authenticated = SessionAuthentication().authenticate(request)
        seen = watched_keys(authenticated[0]) if authenticated else set()
        items = [
            i
            for i in _engine().items(collection, media_type, language)
            if f"{i['media_type']}:{i['tmdb_id']}" not in seen
        ]
        start = (page - 1) * PAGE_SIZE
        response = Response(
            {
                "collection": collection.summary(language),
                "media_type": media_type,
                "page": page,
                "total_pages": max((len(items) + PAGE_SIZE - 1) // PAGE_SIZE, 1),
                "total_results": len(items),
                "results": items[start : start + PAGE_SIZE],
            }
        )
        response["Cache-Control"] = "private, no-store"
        return response


class CollectionRandomView(APIView):
    authentication_classes = PUBLIC_AUTH

    @extend_schema(
        summary="One random title from a collection (Lucky Globe)",
        parameters=[RandomQuerySerializer, LANG_PARAM],
        responses={200: RandomPickResponseSerializer},
        tags=["Collections"],
    )
    @tmdb_unavailable_as_503
    def get(self, request, slug: str):
        collection = get_object_or_404(Collection, slug=slug, is_active=True)
        query = RandomQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        language = get_language(request)
        exclude = {
            key.strip()
            for key in query.validated_data["exclude"].split(",")
            if key.strip()
        }
        if query.validated_data["exclude_watched"]:
            authenticated = SessionAuthentication().authenticate(request)
            if authenticated:
                exclude |= watched_keys(authenticated[0])
        pick = _engine().random_pick(
            collection, query.validated_data["media_type"], language, exclude
        )
        # Never CDN-cached: every spin must be a fresh draw.
        return Response({"collection": collection.summary(language), "pick": pick})
