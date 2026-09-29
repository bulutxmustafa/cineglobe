"""Tests verifying DRF throttling configurations."""

from config.health import HealthCheckView
from rest_framework.throttling import ScopedRateThrottle


def test_health_view_has_throttling_configured():
    """Verify HealthCheckView has ScopedRateThrottle assigned with 'health' scope."""
    view = HealthCheckView()
    assert ScopedRateThrottle in view.throttle_classes
    assert view.throttle_scope == "health"


def test_default_throttle_rates_defined(settings):
    """Verify settings define throttle rates for anon, user, and health scopes."""
    rates = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})
    assert "anon" in rates
    assert "user" in rates
    assert "health" in rates
