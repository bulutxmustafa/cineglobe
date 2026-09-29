"""Tests for unified global exception handling."""

from config.exceptions import (
    _extract_message,
    _get_error_code,
    custom_exception_handler,
)
from rest_framework import exceptions, status
from rest_framework.response import Response


def test_custom_exception_handler_drf_validation():
    """Verify validation errors are shaped into unified error schema."""
    exc = exceptions.ValidationError({"title": ["Bu alan zorunludur."]})
    context = {"view": None, "request": None}
    response = custom_exception_handler(exc, context)

    assert isinstance(response, Response)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.data
    assert "error" in data
    assert data["error"]["status_code"] == 400
    assert "Bu alan zorunludur." in data["error"]["message"]
    assert "title" in data["error"]["details"]


def test_custom_exception_handler_not_found():
    """Verify 404 errors are formatted correctly."""
    exc = exceptions.NotFound("Kaynak bulunamadı.")
    context = {"view": None, "request": None}
    response = custom_exception_handler(exc, context)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.data
    assert data["error"]["code"] == "not_found"
    assert data["error"]["message"] == "Kaynak bulunamadı."
    assert data["error"]["status_code"] == 404


def test_custom_exception_handler_unhandled_500():
    """Verify unhandled exceptions return 500 with sanitized message."""
    exc = RuntimeError("Secret database query crash")
    context = {"view": None, "request": None}
    response = custom_exception_handler(exc, context)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.data
    assert data["error"]["code"] == "internal_server_error"
    assert data["error"]["status_code"] == 500
    assert "Beklenmeyen bir sunucu hatası" in data["error"]["message"]
    assert data["error"]["details"] is None


def test_custom_exception_handler_permission_denied():
    """Verify 403 errors are formatted correctly."""
    exc = exceptions.PermissionDenied("Yetkiniz bulunmamaktadır.")
    context = {"view": None, "request": None}
    response = custom_exception_handler(exc, context)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.data
    assert data["error"]["code"] == "permission_denied"


def test_custom_exception_handler_authentication_failed():
    """Verify 401 errors are formatted correctly."""
    exc = exceptions.AuthenticationFailed("Kimlik doğrulama başarısız.")
    context = {"view": None, "request": None}
    response = custom_exception_handler(exc, context)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.data
    assert data["error"]["code"] == "authentication_failed"


def test_get_error_code_mapping():
    """Verify fallback error code mappings for various HTTP statuses."""

    class DummyExc:
        pass

    assert _get_error_code(DummyExc(), 400) == "validation_error"
    assert _get_error_code(DummyExc(), 401) == "authentication_failed"
    assert _get_error_code(DummyExc(), 403) == "permission_denied"
    assert _get_error_code(DummyExc(), 404) == "not_found"
    assert _get_error_code(DummyExc(), 405) == "method_not_allowed"
    assert _get_error_code(DummyExc(), 429) == "throttled"
    assert _get_error_code(DummyExc(), 500) == "internal_server_error"
    assert _get_error_code(DummyExc(), 503) == "service_unavailable"
    assert _get_error_code(DummyExc(), 418) == "api_error"


def test_extract_message_formats():
    """Verify extraction of error message from various response data formats."""
    assert _extract_message({"detail": "Özel hata"}) == "Özel hata"
    assert _extract_message({"field": ["Liste hatası"]}) == "field: Liste hatası"
    assert _extract_message({"field": "Metin hatası"}) == "field: Metin hatası"
    assert _extract_message({}) == "İstek doğrulanamadı."
    assert _extract_message(["Genel liste hatası"]) == "Genel liste hatası"
    assert _extract_message("Düz string") == "Bir hata oluştu."


def test_unregistered_url_returns_404_json(api_client):
    """Verify non-existent URLs return 404."""
    response = api_client.get("/api/v1/non-existent-endpoint/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
