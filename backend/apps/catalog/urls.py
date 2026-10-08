"""Catalog URL patterns."""

from django.urls import path

from apps.catalog.views import TitleDetailView

urlpatterns = [
    # Title details
    path(
        "titles/<str:media_type>/<int:tmdb_id>/",
        TitleDetailView.as_view(),
        name="title-detail",
    ),
]
