"""Tests for shared query-parameter parsing (lang, page)."""

from unittest.mock import patch

import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url, patch_target",
    [
        ("/api/v1/collections/snack-watch/", "apps.collections.views.TMDBClient"),
        ("/api/v1/upcoming/", "apps.upcoming.views.TMDBClient"),
    ],
)
@pytest.mark.parametrize("page", ["abc", "0", "-1", "501", "1.5"])
def test_invalid_page_returns_400_not_500(api_client, url, patch_target, page):
    """Malformed or out-of-range ?page= must be rejected with a unified 400 error."""
    with patch(patch_target):
        response = api_client.get(url, {"page": page})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"]["status_code"] == 400
    assert "page" in response.json()["error"]["details"]


@pytest.mark.parametrize(
    "header, expected_name_key",
    [
        ("en-US,en;q=0.9", "name_en"),
        ("tr-TR,tr;q=0.9,en;q=0.8", "name_tr"),
        ("de-DE", "name_tr"),
    ],
)
def test_accept_language_header_resolution(api_client, header, expected_name_key):
    """Accept-Language with region/quality values resolves to 'en' or the 'tr' default."""
    response = api_client.get("/api/v1/collections/", HTTP_ACCEPT_LANGUAGE=header)

    assert response.status_code == status.HTTP_200_OK
    collection = response.json()["collections"][0]
    assert collection["name"] == collection[expected_name_key]


def test_lang_query_param_overrides_header(api_client):
    """?lang= takes precedence over the Accept-Language header."""
    response = api_client.get(
        "/api/v1/collections/", {"lang": "en"}, HTTP_ACCEPT_LANGUAGE="tr-TR"
    )

    collection = response.json()["collections"][0]
    assert collection["name"] == collection["name_en"]
