"""Collection URL patterns."""

from django.urls import path

from apps.collections.views import (
    CollectionDetailView,
    CollectionListView,
    CollectionRandomView,
)

urlpatterns = [
    path("", CollectionListView.as_view(), name="collection-list"),
    path("<slug:slug>/", CollectionDetailView.as_view(), name="collection-detail"),
    path(
        "<slug:slug>/random/", CollectionRandomView.as_view(), name="collection-random"
    ),
]
