"""Tests for shared query-parameter parsing (lang, page)."""

from unittest.mock import patch

import pytest
from rest_framework import status


@pytest.mark.parametrize("url", ["/api/v1/categories/cerezlik/", "/api/v1/upcoming/"])
@pytest.mark.parametrize("page", ["abc", "0", "-1", "501", "1.5"])
def test_invalid_page_returns_400_not_500(api_client, url, page):
    """Malformed or out-of-range ?page= must be rejected with a unified 400 error."""
    with patch("apps.catalog.views.TMDBClient"):
        response = api_client.get(url, {"page": page})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"]["status_code"] == 400
    assert "page" in response.json()["error"]["details"]


@pytest.mark.parametrize(
    "header, expected_title_key",
    [
        ("en-US,en;q=0.9", "title_en"),
        ("tr-TR,tr;q=0.9,en;q=0.8", "title_tr"),
        ("de-DE", "title_tr"),
    ],
)
def test_accept_language_header_resolution(api_client, header, expected_title_key):
    """Accept-Language with region/quality values resolves to 'en' or the 'tr' default."""
    response = api_client.get("/api/v1/categories/", HTTP_ACCEPT_LANGUAGE=header)

    assert response.status_code == status.HTTP_200_OK
    category = response.json()["categories"][0]
    assert category["title"] == category[expected_title_key]


def test_lang_query_param_overrides_header(api_client):
    """?lang= takes precedence over the Accept-Language header."""
    response = api_client.get(
        "/api/v1/categories/", {"lang": "en"}, HTTP_ACCEPT_LANGUAGE="tr-TR"
    )

    category = response.json()["categories"][0]
    assert category["title"] == category["title_en"]
