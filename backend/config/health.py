"""Health check endpoint for CineGlobe API monitoring."""

import logging

from django.db import connection
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckResponseSerializer(serializers.Serializer):
    """Schema definition for health check success response."""

    status = serializers.CharField(default="ok")
    db = serializers.CharField(default="ok")


class HealthCheckErrorResponseSerializer(serializers.Serializer):
    """Schema definition for health check error response."""

    status = serializers.CharField(default="error")
    db = serializers.CharField(default="unavailable")
    error = serializers.CharField(required=False)


class HealthCheckView(APIView):
    """API health check endpoint verifying database connectivity and service readiness."""

    permission_classes = []
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "health"

    @extend_schema(
        summary="Sistem ve Veritabanı Sağlık Kontrolü",
        description="Backend ve PostgreSQL veritabanının çalışır durumda olduğunu doğrular.",
        responses={
            200: OpenApiResponse(
                response=HealthCheckResponseSerializer,
                description="Sistem ve veritabanı sağlıklı.",
            ),
            503: OpenApiResponse(
                response=HealthCheckErrorResponseSerializer,
                description="Veritabanı bağlantısı kurulamadı.",
            ),
        },
        tags=["System"],
    )
    def get(self, request, *args, **kwargs):
        """Check database connection and return system status."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
            db_status = "ok"
            http_status = status.HTTP_200_OK
        except Exception as exc:
            logger.error("Health check database probe failed: %s", str(exc))
            db_status = "unavailable"
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE

        response_payload = {
            "status": "ok" if db_status == "ok" else "error",
            "db": db_status,
        }
        return Response(response_payload, status=http_status)
