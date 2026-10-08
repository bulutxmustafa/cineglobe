"""People endpoints: search, best titles, filmography and detail (plan Faz 4)."""

from __future__ import annotations

import logging
from functools import wraps

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.params import get_language, get_page
from apps.catalog.tmdb_client import TMDBClient, TMDBError, TMDBNotFoundError
from apps.people.resolver import PersonResolver, summarize
from apps.people.serializers import (
    FilmographyQuerySerializer,
    FilmographyResponseSerializer,
    PersonDetailSerializer,
    PersonSearchResponseSerializer,
    TopTitlesRequestSerializer,
    TopTitlesResponseSerializer,
)
from apps.people.services import PeopleService

logger = logging.getLogger(__name__)

MESSAGES = {
    "missing_query": {
        "tr": "Arama için 'query' parametresi zorunludur.",
        "en": "The 'query' parameter is required.",
    },
    "person_not_found": {
        "tr": "Bu isimde bir oyuncu bulamadım. Yazımı kontrol edip tam adını yazmayı dene "
        "(örn. 'Robert Downey Jr.').",
        "en": "I couldn't find anyone by that name. Check the spelling or try the full name "
        "(e.g. 'Robert Downey Jr.').",
    },
    "not_found": {
        "tr": "Bu kimliğe sahip bir kişi bulunamadı.",
        "en": "No person exists with this id.",
    },
    "service_unavailable": {
        "tr": "Film veritabanı (TMDB) şu anda erişilemiyor. Lütfen kısa süre sonra tekrar deneyin.",
        "en": "The movie database (TMDB) is currently unavailable. Please try again shortly.",
    },
}

LANG_PARAM = OpenApiParameter("lang", str, enum=["tr", "en"], default="tr")


def _error(code: str, language: str, http_status: int, details=None) -> Response:
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


def _tmdb() -> TMDBClient:
    try:
        return TMDBClient()
    except ValueError as exc:  # TMDB_API_KEY missing: a server problem, not a 500
        raise TMDBError(str(exc)) from exc


def tmdb_errors(view_method):
    """Map TMDB failures to the unified 404/503 error format."""

    @wraps(view_method)
    def wrapper(self, request, *args, **kwargs):
        language = get_language(request)
        try:
            return view_method(self, request, *args, **kwargs)
        except TMDBNotFoundError:
            return _error("not_found", language, status.HTTP_404_NOT_FOUND)
        except TMDBError as exc:
            logger.error("TMDB failure in %s: %s", type(self).__name__, exc)
            return _error(
                "service_unavailable", language, status.HTTP_503_SERVICE_UNAVAILABLE
            )

    return wrapper


class PersonSearchView(APIView):
    @extend_schema(
        summary="Search people by name",
        parameters=[OpenApiParameter("query", str, required=True), LANG_PARAM],
        responses={200: PersonSearchResponseSerializer},
        tags=["People"],
    )
    @tmdb_errors
    def get(self, request):
        language = get_language(request)
        query = request.query_params.get("query", "").strip()
        if not query:
            return _error("missing_query", language, status.HTTP_400_BAD_REQUEST)
        results = _tmdb().search_person(query).get("results", [])
        people = [summarize(p) for p in results if not p.get("adult")][:10]
        return Response({"query": query, "count": len(people), "results": people})


class TopTitlesView(APIView):
    @extend_schema(
        summary="A person's best movies and series",
        description=(
            "Resolves a name (nicknames like 'RDJ' and small typos included) and returns "
            "lead roles above the vote threshold, guest spots and self-appearances removed. "
            "If several people share the name, status='ambiguous' with candidates."
        ),
        request=TopTitlesRequestSerializer,
        responses={
            200: TopTitlesResponseSerializer,
            404: OpenApiResponse(description="No person found (with a suggestion)"),
            503: OpenApiResponse(description="TMDB unavailable"),
        },
        tags=["People"],
    )
    @tmdb_errors
    def post(self, request):
        serializer = TopTitlesRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        language = data.get("lang") or get_language(request)
        client = _tmdb()

        if data.get("person_id"):
            detail = client.get_person_details(data["person_id"], language=language)
            payload = {
                "status": "found",
                "query": "",
                "person": summarize(detail),
                "candidates": [],
            }
        else:
            resolved = PersonResolver(client).resolve(data["name"])
            if resolved.status == "not_found":
                return _error(
                    "person_not_found",
                    language,
                    status.HTTP_404_NOT_FOUND,
                    details={"query": resolved.query},
                )
            payload = resolved.as_dict()
            if resolved.status == "ambiguous":
                return Response(payload)

        payload["media_type"] = data["media_type"]
        payload["sections"] = PeopleService(client).top_titles(
            payload["person"]["tmdb_id"], data["media_type"], language
        )
        return Response(payload)


class PersonDetailView(APIView):
    @extend_schema(
        summary="Person detail (biography falls back to English)",
        parameters=[LANG_PARAM],
        responses={200: PersonDetailSerializer},
        tags=["People"],
    )
    @tmdb_errors
    def get(self, request, person_id: int):
        language = get_language(request)
        return Response(PeopleService(_tmdb()).detail(person_id, language))


class FilmographyView(APIView):
    @extend_schema(
        summary="Full filmography: newest / oldest / rating / popularity",
        parameters=[
            FilmographyQuerySerializer,
            OpenApiParameter("page", int, default=1),
            LANG_PARAM,
        ],
        responses={200: FilmographyResponseSerializer},
        tags=["People"],
    )
    @tmdb_errors
    def get(self, request, person_id: int):
        query = FilmographyQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        language = get_language(request)
        client = _tmdb()
        detail = client.get_person_details(person_id, language=language)
        payload = PeopleService(client).filmography(
            person_id, page=get_page(request), language=language, **query.validated_data
        )
        return Response({"person": summarize(detail), **payload})
