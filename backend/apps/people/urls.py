"""URL patterns for people & actor endpoints."""

from django.urls import path

from apps.people.views import PersonCreditsView, PersonDetailView, PersonSearchView

urlpatterns = [
    path("search/", PersonSearchView.as_view(), name="person-search"),
    path("<int:person_id>/", PersonDetailView.as_view(), name="person-detail"),
    path(
        "<int:person_id>/credits/", PersonCreditsView.as_view(), name="person-credits"
    ),
]
