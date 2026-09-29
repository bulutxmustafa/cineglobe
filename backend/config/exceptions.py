"""Custom global exception handler for consistent JSON error responses across CineGlobe API."""

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Transform DRF and unhandled exceptions into a unified, predictable JSON error format.

    Format:
    {
        "error": {
            "code": "error_code_string",
            "message": "Human readable summary",
            "status_code": 400,
            "details": { ... } or null
        }
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        status_code = response.status_code
        error_code = _get_error_code(exc, status_code)
        message = _extract_message(response.data)

        custom_data = {
            "error": {
                "code": error_code,
                "message": message,
                "status_code": status_code,
                "details": (
                    response.data
                    if isinstance(response.data, dict)
                    else {"non_field_errors": response.data}
                ),
            }
        }
        response.data = custom_data
        return response

    # Unhandled 500 errors
    logger.exception("Unhandled server exception: %s", str(exc), exc_info=exc)
    return Response(
        {
            "error": {
                "code": "internal_server_error",
                "message": "Beklenmeyen bir sunucu hatası oluştu.",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "details": None,
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _get_error_code(exc, status_code: int) -> str:
    """Determine a machine-readable error code string."""
    if hasattr(exc, "default_code"):
        return str(exc.default_code)

    code_map = {
        400: "validation_error",
        401: "authentication_failed",
        403: "permission_denied",
        404: "not_found",
        405: "method_not_allowed",
        429: "throttled",
        500: "internal_server_error",
        503: "service_unavailable",
    }
    return code_map.get(status_code, "api_error")


def _extract_message(data) -> str:
    """Extract a user-friendly string message from error details."""
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        # Return first error message found
        for key, val in data.items():
            if isinstance(val, list) and len(val) > 0:
                return f"{key}: {val[0]}"
            if isinstance(val, str):
                return f"{key}: {val}"
        return "İstek doğrulanamadı."
    elif isinstance(data, list) and len(data) > 0:
        return str(data[0])
    return "Bir hata oluştu."
