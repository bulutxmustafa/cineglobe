"""TMDB API client with retry, timeout, rate-limit respect, error handling, and multi-language support (TR & EN).

All external TMDB calls go through this class. Tests should mock this class
rather than making live HTTP requests.

Cache strategy (per §3 of CINEGLOBE_PLAN.md):
    - Movie/TV detail:            24 hours
    - Ongoing TV show detail:      6 hours  (new episodes/seasons change frequently)
    - Discover / search results:   1 hour
    - Person combined_credits:    24 hours
"""

import hashlib
import json
import logging
from typing import Any

import httpx
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Cache TTLs in seconds
TTL_DETAIL = 60 * 60 * 24  # 24 hours
TTL_DETAIL_ONGOING_TV = 60 * 60 * 6  # 6 hours
TTL_DISCOVER = 60 * 60  # 1 hour
TTL_PERSON = 60 * 60 * 24  # 24 hours

# Endpoints whose results can contain adult titles unless filtered.
ADULT_FILTERED_PREFIXES = ("/discover/", "/search/")

# HTTP client settings
DEFAULT_TIMEOUT = 10.0  # seconds
MAX_RETRIES = 3


def normalize_language(language: str | None) -> str:
    """Normalize language code to TMDB supported format (tr-TR or en-US)."""
    if not language:
        return "tr-TR"
    lang_lower = language.lower().strip()
    if lang_lower.startswith("en"):
        return "en-US"
    return "tr-TR"


class TMDBError(Exception):
    """Base exception for all TMDB client errors."""


class TMDBRateLimitError(TMDBError):
    """Raised when TMDB returns HTTP 429 Too Many Requests."""


class TMDBServiceUnavailableError(TMDBError):
    """Raised when TMDB is unreachable or returns 5xx errors."""


class TMDBNotFoundError(TMDBError):
    """Raised when a TMDB resource is not found (HTTP 404)."""


class TMDBClient:
    """Thin wrapper around the TMDB v3 REST API.

    - All requests are authenticated with the API key from settings.
    - Responses are cached using Django's cache framework.
    - Transient network errors are retried up to MAX_RETRIES times.
    - Rate limit (429) and server errors (5xx) raise descriptive exceptions
      that callers can catch and convert to 503 Service Unavailable.
    - Supports both Turkish ('tr-TR') and English ('en-US') locales.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.TMDB_API_KEY
        if not self._api_key:
            raise ValueError("TMDB_API_KEY is not set. Add it to your .env file.")
        self._client = httpx.Client(
            base_url=TMDB_BASE_URL,
            timeout=DEFAULT_TIMEOUT,
            headers={"Accept": "application/json"},
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_movie_detail(self, tmdb_id: int, language: str = "tr-TR") -> dict[str, Any]:
        """Fetch full movie detail with language support. Cached for 24 hours."""
        lang = normalize_language(language)
        cache_key = self._key("movie", tmdb_id, lang, "detail")
        return self._cached_get(
            f"/movie/{tmdb_id}",
            params={"append_to_response": "keywords", "language": lang},
            cache_key=cache_key,
            ttl=TTL_DETAIL,
        )

    def get_tv_detail(self, tmdb_id: int, language: str = "tr-TR") -> dict[str, Any]:
        """Fetch full TV show detail. Cached for 24h or 6h if still airing."""
        lang = normalize_language(language)
        cache_key = self._key("tv", tmdb_id, lang, "detail")
        data = self._cached_get(
            f"/tv/{tmdb_id}",
            params={"append_to_response": "keywords", "language": lang},
            cache_key=cache_key,
            ttl=TTL_DETAIL,  # default; overridden below for ongoing shows
        )
        # Override TTL for ongoing/in-production shows
        if data.get("in_production") or data.get("status") in (
            "Returning Series",
            "In Production",
        ):
            cache.set(cache_key, data, TTL_DETAIL_ONGOING_TV)
        return data

    def discover_movies(
        self, params: dict[str, Any], language: str = "tr-TR"
    ) -> dict[str, Any]:
        """Run a movie discover query. Cached for 1 hour."""
        lang = normalize_language(language)
        merged_params = {"language": lang, **params}
        cache_key = self._params_key(f"discover_movie_{lang}", merged_params)
        return self._cached_get(
            "/discover/movie",
            params=merged_params,
            cache_key=cache_key,
            ttl=TTL_DISCOVER,
        )

    def discover_tv(
        self, params: dict[str, Any], language: str = "tr-TR"
    ) -> dict[str, Any]:
        """Run a TV discover query. Cached for 1 hour."""
        lang = normalize_language(language)
        merged_params = {"language": lang, **params}
        cache_key = self._params_key(f"discover_tv_{lang}", merged_params)
        return self._cached_get(
            "/discover/tv",
            params=merged_params,
            cache_key=cache_key,
            ttl=TTL_DISCOVER,
        )

    def search_person(self, query: str) -> dict[str, Any]:
        """Search for a person by name. Cached 24 hours."""
        params = {"query": query}
        return self._cached_get(
            "/search/person",
            params=params,
            cache_key=self._params_key("person_search", params),
            ttl=TTL_PERSON,
        )

    def get_person_details(
        self, person_id: int, language: str = "tr-TR"
    ) -> dict[str, Any]:
        """Fetch full details of a person/actor. Cached for 24 hours."""
        lang = normalize_language(language)
        cache_key = self._key("person", person_id, lang, "details")
        return self._cached_get(
            f"/person/{person_id}",
            params={"language": lang},
            cache_key=cache_key,
            ttl=TTL_PERSON,
        )

    def get_person_combined_credits(
        self, person_id: int, language: str = "tr-TR"
    ) -> dict[str, Any]:
        """Fetch cast + crew credits across movies AND TV shows. Cached 24h."""
        lang = normalize_language(language)
        cache_key = self._key("person", person_id, lang, "combined_credits")
        return self._cached_get(
            f"/person/{person_id}/combined_credits",
            params={"language": lang},
            cache_key=cache_key,
            ttl=TTL_PERSON,
        )

    def search_keyword(self, query: str) -> dict[str, Any]:
        """Search TMDB for keyword IDs matching a string."""
        cache_key = self._params_key("keyword_search", {"q": query})
        return self._cached_get(
            "/search/keyword",
            params={"query": query},
            cache_key=cache_key,
            ttl=TTL_DISCOVER,
        )

    def get_popular_movies(
        self, page: int = 1, language: str = "tr-TR"
    ) -> dict[str, Any]:
        """Fetch a page of popular movies. Cached 1 hour."""
        lang = normalize_language(language)
        cache_key = self._key("popular_movies", page, lang)
        return self._cached_get(
            "/movie/popular",
            params={"page": page, "language": lang},
            cache_key=cache_key,
            ttl=TTL_DISCOVER,
        )

    def get_popular_tv(self, page: int = 1, language: str = "tr-TR") -> dict[str, Any]:
        """Fetch a page of popular TV shows. Cached 1 hour."""
        lang = normalize_language(language)
        cache_key = self._key("popular_tv", page, lang)
        return self._cached_get(
            "/tv/popular",
            params={"page": page, "language": lang},
            cache_key=cache_key,
            ttl=TTL_DISCOVER,
        )

    def get_upcoming_movies(
        self, page: int = 1, language: str = "tr-TR"
    ) -> dict[str, Any]:
        """Fetch upcoming movie releases. Cached 6 hours."""
        lang = normalize_language(language)
        cache_key = self._key("upcoming_movies", page, lang)
        return self._cached_get(
            "/movie/upcoming",
            params={"page": page, "language": lang},
            cache_key=cache_key,
            ttl=TTL_DETAIL_ONGOING_TV,
        )

    def get_upcoming_tv(self, page: int = 1, language: str = "tr-TR") -> dict[str, Any]:
        """Fetch upcoming TV shows airing in the future. Cached 6 hours."""
        from datetime import date

        today = date.today().isoformat()
        lang = normalize_language(language)
        cache_key = self._key("upcoming_tv", page, lang, today)
        return self._cached_get(
            "/discover/tv",
            params={
                "page": page,
                "language": lang,
                "first_air_date.gte": today,
                "sort_by": "first_air_date.asc",
            },
            cache_key=cache_key,
            ttl=TTL_DETAIL_ONGOING_TV,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cached_get(
        self,
        path: str,
        params: dict[str, Any],
        cache_key: str,
        ttl: int,
    ) -> dict[str, Any]:
        """Return cached result if available, otherwise fetch and cache."""
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug("TMDB cache hit: %s", cache_key)
            return cached

        data = self._get(path, params=params)
        cache.set(cache_key, data, ttl)
        return data

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute GET request against TMDB with retries and error normalisation."""
        all_params = {"api_key": self._api_key, **(params or {})}
        if path.startswith(ADULT_FILTERED_PREFIXES):
            # Plan v1.7: adult titles never enter search, lists or the globe.
            all_params["include_adult"] = "false"
        last_exc: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._client.get(path, params=all_params)

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 404:
                    raise TMDBNotFoundError(f"TMDB resource not found: {path}")

                if response.status_code == 401:
                    raise TMDBError("Invalid TMDB API key (HTTP 401).")

                if response.status_code == 429:
                    raise TMDBRateLimitError(
                        "TMDB rate limit exceeded. Retry after a short delay."
                    )

                if response.status_code >= 500:
                    raise TMDBServiceUnavailableError(
                        f"TMDB server error {response.status_code} on {path}"
                    )

                raise TMDBError(
                    f"Unexpected TMDB status {response.status_code} on {path}"
                )

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_exc = exc
                logger.warning(
                    "TMDB request attempt %d/%d failed (%s): %s",
                    attempt,
                    MAX_RETRIES,
                    path,
                    exc,
                )
                if attempt == MAX_RETRIES:
                    raise TMDBServiceUnavailableError(
                        f"TMDB unreachable after {MAX_RETRIES} attempts: {exc}"
                    ) from exc

            except (TMDBNotFoundError, TMDBRateLimitError, TMDBError):
                raise

        # Should not reach here
        raise TMDBServiceUnavailableError(  # pragma: no cover
            f"TMDB request failed: {last_exc}"
        )

    # ------------------------------------------------------------------
    # Cache key factories
    # ------------------------------------------------------------------

    @staticmethod
    def _key(*parts: Any) -> str:
        """Build a simple namespaced cache key."""
        return "tmdb:" + ":".join(str(p) for p in parts)

    @staticmethod
    def _params_key(prefix: str, params: dict[str, Any]) -> str:
        """Build a stable cache key from a dict of query parameters."""
        serialised = json.dumps(params, sort_keys=True)
        digest = hashlib.sha256(serialised.encode()).hexdigest()[:16]
        return f"tmdb:{prefix}:{digest}"
