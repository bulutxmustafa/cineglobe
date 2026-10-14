"""Pytest shared test fixtures for CineGlobe backend test suite."""

import os

import django
import pytest
from rest_framework.test import APIClient


def pytest_configure():
    """Ensure Django is initialized before running tests."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    django.setup()


@pytest.fixture
def api_client():
    """Return an unauthenticated DRF API client."""
    return APIClient()


@pytest.fixture(autouse=True)
def _no_image_downloads(monkeypatch):
    """Tests never download TMDB images; the backdrop check then keeps the default."""

    def offline(url):
        raise OSError("image downloads are disabled in tests")

    monkeypatch.setattr("apps.catalog.backdrops.load_image", offline)
