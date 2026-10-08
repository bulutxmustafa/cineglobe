"""Notebook URL patterns (mounted at /api/v1/me/notebook/)."""

from django.urls import path

from apps.notebook import views

urlpatterns = [
    path("", views.NotebookListView.as_view(), name="notebook"),
    path("lookup/", views.NotebookLookupView.as_view(), name="notebook-lookup"),
    path("stats/", views.NotebookStatsView.as_view(), name="notebook-stats"),
    path("export/", views.NotebookExportView.as_view(), name="notebook-export"),
    path("merge/", views.NotebookMergeView.as_view(), name="notebook-merge"),
    path(
        "<str:media_type>/<int:tmdb_id>/",
        views.NotebookEntryView.as_view(),
        name="notebook-entry",
    ),
]
