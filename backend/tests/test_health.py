"""Tests for health check endpoint."""

from unittest.mock import patch

import pytest
from rest_framework import status


@pytest.mark.django_db
def test_health_check_success(api_client):
    """Test health check returns 200 OK and status ok when DB is operational."""
    with patch("django.db.connection.cursor") as mock_cursor:
        mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (1,)
        response = api_client.get("/api/v1/health/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status": "ok",
        "db": "ok",
    }


def test_health_check_db_failure(api_client):
    """Test health check returns 503 and unavailable status when DB probe fails."""
    with patch(
        "django.db.connection.cursor",
        side_effect=Exception("Database connection timeout"),
    ):
        response = api_client.get("/api/v1/health/")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["status"] == "error"
    assert data["db"] == "unavailable"


def test_health_check_method_not_allowed(api_client):
    """Test unsupported HTTP method on health endpoint returns 405 with structured error."""
    response = api_client.post("/api/v1/health/", data={})
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "method_not_allowed"
    assert data["error"]["status_code"] == 405
