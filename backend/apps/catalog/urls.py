"""Catalog URL patterns."""

from django.urls import path

from apps.catalog.views import PopularView, TitleDetailView

urlpatterns = [
    path("popular/", PopularView.as_view(), name="popular"),
    # Title details
    path(
        "titles/<str:media_type>/<int:tmdb_id>/",
        TitleDetailView.as_view(),
        name="title-detail",
    ),
]
