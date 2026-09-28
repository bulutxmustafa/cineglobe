"""Tests verifying environment settings separation and configurations."""

import importlib

import config.settings.dev as dev_settings
import pytest
from django.conf import settings


def test_dev_settings_loaded():
    """Verify that development settings load successfully with appropriate defaults."""
    # pytest-django sets django.conf.settings.DEBUG to False by design for testing,
    # so we check the dev settings module configuration directly.
    assert dev_settings.DEBUG is True
    assert "apps.catalog" in settings.INSTALLED_APPS
    assert "apps.search" in settings.INSTALLED_APPS
    assert "apps.people" in settings.INSTALLED_APPS
    assert "apps.accounts" in settings.INSTALLED_APPS
    assert "rest_framework" in settings.INSTALLED_APPS
    assert "drf_spectacular" in settings.INSTALLED_APPS
    assert "corsheaders" in settings.INSTALLED_APPS
    assert (
        settings.REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"]
        == "drf_spectacular.openapi.AutoSchema"
    )
    assert (
        settings.REST_FRAMEWORK["EXCEPTION_HANDLER"]
        == "config.exceptions.custom_exception_handler"
    )


def test_base_settings_loads_cleanly():
    """Verify that base settings module can be imported independently."""
    base_module = importlib.import_module("config.settings.base")
    assert hasattr(base_module, "BASE_DIR")
    assert hasattr(base_module, "INSTALLED_APPS")
    assert hasattr(base_module, "DATABASES")
    assert hasattr(base_module, "SPECTACULAR_SETTINGS")


def test_prod_settings_enforces_secure_secret_key(monkeypatch):
    """Verify prod settings raise ValueError if insecure default secret key is used."""
    monkeypatch.setenv("DJANGO_SECRET_KEY", "insecure-default-change-in-production")

    with pytest.raises(
        ValueError, match="DJANGO_SECRET_KEY must be properly set in production"
    ):
        # Reload base then prod to test rejection
        import config.settings.base

        importlib.reload(config.settings.base)
        import config.settings.prod

        importlib.reload(config.settings.prod)
