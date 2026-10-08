"""Views for people/actor endpoints: search, details, and chronological/recent filmography."""

import logging
from typing import Any

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.tmdb_client import (
    TMDBClient,
    TMDBNotFoundError,
    TMDBServiceUnavailableError,
)
from apps.people.serializers import PersonCreditItemSerializer, PersonDetailSerializer

logger = logging.getLogger(__name__)


class PersonSearchView(APIView):
    """Search for actors and directors by name."""

    @extend_schema(
        summary="Search actors or people",
        parameters=[
            OpenApiParameter(
                "query",
                location=OpenApiParameter.QUERY,
                type=str,
                required=True,
                description="Name of person",
            ),
            OpenApiParameter(
                "lang", location=OpenApiParameter.QUERY, type=str, default="tr"
            ),
        ],
        tags=["People"],
    )
    def get(self, request):
        query = request.query_params.get("query", "").strip()
        if not query:
            return Response(
                {
                    "error": {
                        "code": "missing_query",
                        "message": "Arama için 'query' parametresi zorunludur.",
                        "status_code": 400,
                        "details": None,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        client = TMDBClient()
        try:
            data = client.search_person(query)
        except TMDBServiceUnavailableError as exc:
            logger.error("TMDB error in person search: %s", exc)
            return Response(
                {
                    "error": {
                        "code": "service_unavailable",
                        "message": "Kişi araması şu anda gerçekleştirilemiyor.",
                        "status_code": 503,
                        "details": None,
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        results = data.get("results", [])
        return Response({"query": query, "count": len(results), "results": results})


class PersonDetailView(APIView):
    """Retrieve full details for an actor or person."""

    @extend_schema(
        summary="Get person biography and details",
        parameters=[
            OpenApiParameter("person_id", location=OpenApiParameter.PATH, type=int),
            OpenApiParameter(
                "lang", location=OpenApiParameter.QUERY, type=str, default="tr"
            ),
        ],
        responses={200: PersonDetailSerializer},
        tags=["People"],
    )
    def get(self, request, person_id: int):
        lang = request.query_params.get("lang") or request.headers.get(
            "Accept-Language", "tr"
        )
        client = TMDBClient()

        try:
            details = client.get_person_details(person_id, language=lang)
        except TMDBNotFoundError:
            return Response(
                {
                    "error": {
                        "code": "not_found",
                        "message": f"{person_id} kimlikli kişi bulunamadı.",
                        "status_code": 404,
                        "details": None,
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except TMDBServiceUnavailableError as exc:
            logger.error("TMDB error in person detail: %s", exc)
            return Response(
                {
                    "error": {
                        "code": "service_unavailable",
                        "message": "Kişi bilgileri şu anda alınamıyor.",
                        "status_code": 503,
                        "details": None,
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer = PersonDetailSerializer(details)
        return Response(serializer.data)


class PersonCreditsView(APIView):
    """Retrieve an actor's filmography sorted chronologically, by recency, or by rating."""

    @extend_schema(
        summary="Get actor filmography sorted chronologically or by rating",
        parameters=[
            OpenApiParameter("person_id", location=OpenApiParameter.PATH, type=int),
            OpenApiParameter(
                "sort_by",
                location=OpenApiParameter.QUERY,
                type=str,
                enum=["recent", "chronological_asc", "top_rated", "popular"],
                default="recent",
                description="Sorting order: recent (newest/upcoming first), chronological_asc (oldest to newest), top_rated, or popular",
            ),
            OpenApiParameter(
                "media_type",
                location=OpenApiParameter.QUERY,
                type=str,
                enum=["both", "movie", "tv"],
                default="both",
                description="Filter by media type: both, movie, or tv",
            ),
            OpenApiParameter(
                "lang", location=OpenApiParameter.QUERY, type=str, default="tr"
            ),
        ],
        tags=["People"],
    )
    def get(self, request, person_id: int):
        sort_by = request.query_params.get("sort_by", "recent")
        media_type = request.query_params.get("media_type", "both")
        lang = request.query_params.get("lang") or request.headers.get(
            "Accept-Language", "tr"
        )

        client = TMDBClient()

        try:
            person_details = client.get_person_details(person_id, language=lang)
            credits_data = client.get_person_combined_credits(person_id, language=lang)
        except TMDBNotFoundError:
            return Response(
                {
                    "error": {
                        "code": "not_found",
                        "message": f"{person_id} kimlikli kişi bulunamadı.",
                        "status_code": 404,
                        "details": None,
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except TMDBServiceUnavailableError as exc:
            logger.error("TMDB error in person credits: %s", exc)
            return Response(
                {
                    "error": {
                        "code": "service_unavailable",
                        "message": "Filmografi verisi şu anda alınamıyor.",
                        "status_code": 503,
                        "details": None,
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        cast_items = credits_data.get("cast", [])

        # Filter by media type if requested
        if media_type in ("movie", "tv"):
            filtered_items = [
                item for item in cast_items if item.get("media_type") == media_type
            ]
        else:
            filtered_items = list(cast_items)

        # Sort the filmography
        sorted_items = self._sort_credits(filtered_items, sort_by=sort_by)

        serializer = PersonCreditItemSerializer(sorted_items, many=True)

        return Response(
            {
                "person": {
                    "id": person_details.get("id"),
                    "name": person_details.get("name"),
                    "profile_path": person_details.get("profile_path"),
                },
                "sort_by": sort_by,
                "media_type": media_type,
                "total_credits": len(sorted_items),
                "credits": serializer.data,
            }
        )

    def _sort_credits(
        self, items: list[dict[str, Any]], sort_by: str
    ) -> list[dict[str, Any]]:
        """Sort filmography items according to specified criterion."""

        def get_date(item: dict[str, Any]) -> str:
            return item.get("release_date") or item.get("first_air_date") or ""

        if sort_by == "chronological_asc":
            # Oldest to newest (empty dates placed at the end)
            return sorted(items, key=lambda x: get_date(x) or "9999-99-99")

        elif sort_by == "top_rated":
            # Best ratings with reasonable vote count priority
            return sorted(
                items,
                key=lambda x: (
                    x.get("vote_count", 0) >= 50,
                    x.get("vote_average", 0.0),
                    x.get("vote_count", 0),
                ),
                reverse=True,
            )

        elif sort_by == "popular":
            # By TMDB popularity
            return sorted(items, key=lambda x: x.get("popularity", 0.0), reverse=True)

        else:  # 'recent' / chronological_desc
            # Newest/upcoming to oldest (empty dates placed at the bottom)
            return sorted(
                items, key=lambda x: get_date(x) or "0000-00-00", reverse=True
            )
