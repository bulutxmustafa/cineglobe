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
