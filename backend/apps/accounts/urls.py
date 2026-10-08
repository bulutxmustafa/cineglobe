"""Account URL patterns (mounted at /api/v1/)."""

from django.urls import path

from apps.accounts import views

urlpatterns = [
    path("auth/csrf/", views.CsrfView.as_view(), name="auth-csrf"),
    path("auth/register/", views.RegisterView.as_view(), name="auth-register"),
    path("auth/login/", views.LoginView.as_view(), name="auth-login"),
    path("auth/logout/", views.LogoutView.as_view(), name="auth-logout"),
    path(
        "auth/password/change/",
        views.PasswordChangeView.as_view(),
        name="auth-password-change",
    ),
    path(
        "auth/password/reset/",
        views.PasswordResetRequestView.as_view(),
        name="auth-password-reset",
    ),
    path(
        "auth/password/reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
    path("auth/unsubscribe/", views.UnsubscribeView.as_view(), name="auth-unsubscribe"),
    path("me/", views.MeView.as_view(), name="me"),
    path("me/export/", views.ExportView.as_view(), name="me-export"),
    path(
        "me/search-history/",
        views.SearchHistoryView.as_view(),
        name="me-search-history",
    ),
    path(
        "me/search-history/<int:pk>/",
        views.SearchHistoryItemView.as_view(),
        name="me-search-history-item",
    ),
    path(
        "me/notifications/", views.NotificationsView.as_view(), name="me-notifications"
    ),
]
