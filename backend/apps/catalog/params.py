"""Shared query-parameter parsing helpers for API views."""

from rest_framework.exceptions import ValidationError
from rest_framework.request import Request

# TMDB rejects page numbers above 500.
MAX_PAGE = 500


def get_language(request: Request) -> str:
    """Resolve the response language ('tr' or 'en') from ?lang= or Accept-Language."""
    raw = request.query_params.get("lang") or request.headers.get("Accept-Language", "")
    return "en" if raw.lower().strip().startswith("en") else "tr"


def get_page(request: Request) -> int:
    """Parse ?page= as an integer in [1, MAX_PAGE]; raise 400 on invalid input."""
    raw = request.query_params.get("page", "1")
    try:
        page = int(raw)
    except (TypeError, ValueError):
        raise ValidationError({"page": "page must be a positive integer."}) from None
    if not 1 <= page <= MAX_PAGE:
        raise ValidationError({"page": f"page must be between 1 and {MAX_PAGE}."})
    return page
