"""Tests for OpenAPI schema and documentation endpoints."""

from rest_framework import status


def test_schema_endpoint_returns_valid_openapi(api_client):
    """Verify /api/schema/ returns OpenAPI 3.0 schema."""
    response = api_client.get("/api/schema/")
    assert response.status_code == status.HTTP_200_OK
    assert "openapi" in response.data or "openapi" in str(response.content)


def test_swagger_ui_endpoint_accessible(api_client):
    """Verify Swagger UI documentation page loads successfully."""
    response = api_client.get("/api/schema/swagger-ui/")
    assert response.status_code == status.HTTP_200_OK
    assert "swagger-ui" in response.content.decode("utf-8").lower()


def test_redoc_endpoint_accessible(api_client):
    """Verify ReDoc documentation page loads successfully."""
    response = api_client.get("/api/schema/redoc/")
    assert response.status_code == status.HTTP_200_OK
    assert "redoc" in response.content.decode("utf-8").lower()
