"""Social URL patterns (mounted at /api/v1/)."""

from django.urls import path

from apps.social import views

urlpatterns = [
    # Owner
    path("me/profile/", views.MyProfileView.as_view(), name="my-profile"),
    path("me/lists/", views.MyListsView.as_view(), name="my-lists"),
    path("me/lists/<int:pk>/", views.MyListView.as_view(), name="my-list"),
    path(
        "me/lists/<int:pk>/items/",
        views.MyListItemsView.as_view(),
        name="my-list-items",
    ),
    path("me/shares/", views.MySharesView.as_view(), name="my-shares"),
    path("me/shares/<int:pk>/", views.MyShareView.as_view(), name="my-share"),
    path("me/blocks/", views.MyBlocksView.as_view(), name="my-blocks"),
    path("me/blocks/<str:username>/", views.MyBlockView.as_view(), name="my-block"),
    # Public reads (no account needed)
    path(
        "users/<str:username>/",
        views.PublicProfileView.as_view(),
        name="public-profile",
    ),
    path("lists/<str:slug>/", views.PublicListView.as_view(), name="public-list"),
    path(
        "lists/<str:slug>/random/",
        views.PublicListRandomView.as_view(),
        name="public-list-random",
    ),
    path("lists/<str:slug>/clone/", views.CloneListView.as_view(), name="clone-list"),
    path(
        "shared/<str:token>/",
        views.SharedNotebookView.as_view(),
        name="shared-notebook",
    ),
    path(
        "titles/<str:media_type>/<int:tmdb_id>/community/",
        views.CommunityView.as_view(),
        name="title-community",
    ),
    path("reports/", views.ReportView.as_view(), name="reports"),
]
