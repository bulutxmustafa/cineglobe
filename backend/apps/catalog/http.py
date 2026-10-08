"""HTTP helpers shared by public API views."""

from __future__ import annotations

from django.utils.cache import patch_vary_headers
from rest_framework.request import Request
from rest_framework.response import Response


def cdn_cache(response: Response, request: Request, seconds: int) -> Response:
    """Let the platform CDN (Vercel) cache a public GET response.

    Repeat requests are then answered by the CDN without waking the Django
    function or the Neon database, which protects the free compute quota
    (plan v1.8, docs/cost.md). Only applied when the language is explicit in
    the URL: the CDN keys on the URL, so a response whose language came from
    the Accept-Language header must not be shared.
    """
    if request.method != "GET" or response.status_code != 200:
        return response
    patch_vary_headers(response, ["Accept-Language"])
    if "lang" in request.query_params:
        response["Cache-Control"] = (
            f"public, max-age=0, s-maxage={seconds}, stale-while-revalidate={seconds}"
        )
    else:
        response["Cache-Control"] = "private, max-age=0"
    return response
