"""Catalog URL patterns."""

from django.urls import path

from apps.catalog.views import (
    GuideDetailView,
    GuideListView,
    PopularView,
    TitleDetailView,
    TitleTrailerView,
)

urlpatterns = [
    path("popular/", PopularView.as_view(), name="popular"),
    path("guides/", GuideListView.as_view(), name="guide-list"),
    path("guides/<slug:slug>/", GuideDetailView.as_view(), name="guide-detail"),
    # Title details
    path(
        "titles/<str:media_type>/<int:tmdb_id>/",
        TitleDetailView.as_view(),
        name="title-detail",
    ),
    path(
        "titles/<str:media_type>/<int:tmdb_id>/trailer/",
        TitleTrailerView.as_view(),
        name="title-trailer",
    ),
]
