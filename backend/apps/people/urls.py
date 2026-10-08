"""URL patterns for people endpoints."""

from django.urls import path

from apps.people.views import (
    FilmographyView,
    PersonDetailView,
    PersonSearchView,
    TopTitlesView,
)

urlpatterns = [
    path("search/", PersonSearchView.as_view(), name="person-search"),
    path("top-titles/", TopTitlesView.as_view(), name="person-top-titles"),
    path("<int:person_id>/", PersonDetailView.as_view(), name="person-detail"),
    path(
        "<int:person_id>/filmography/",
        FilmographyView.as_view(),
        name="person-filmography",
    ),
]
