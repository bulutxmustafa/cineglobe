"""Catalog URL patterns."""

from django.urls import path

from apps.catalog.views import (
    CuratedCategoryDetailView,
    CuratedCategoryListView,
    TitleDetailView,
    UpcomingTitlesView,
)

urlpatterns = [
    # Title details
    path(
        "titles/<str:media_type>/<int:tmdb_id>/",
        TitleDetailView.as_view(),
        name="title-detail",
    ),
    # Curated / mood categories
    path(
        "categories/",
        CuratedCategoryListView.as_view(),
        name="curated-category-list",
    ),
    path(
        "categories/<str:slug>/",
        CuratedCategoryDetailView.as_view(),
        name="curated-category-detail",
    ),
    # Upcoming releases
    path(
        "upcoming/",
        UpcomingTitlesView.as_view(),
        name="upcoming-titles",
    ),
]
