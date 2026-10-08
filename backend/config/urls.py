"""URL configuration for CineGlobe project."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from config.health import HealthCheckView

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Health check
    path("api/v1/health/", HealthCheckView.as_view(), name="health-check"),
    # Catalog (movies, tv shows, curated categories, upcoming)
    path("api/v1/", include("apps.catalog.urls")),
    # Upcoming releases
    path("api/v1/upcoming/", include("apps.upcoming.urls")),
    # Curated collections
    path("api/v1/collections/", include("apps.collections.urls")),
    # Natural-language search
    path("api/v1/search/", include("apps.search.urls")),
    # People (actors, directors, filmography)
    path("api/v1/people/", include("apps.people.urls")),
    # OpenAPI Schema and Interactive Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
