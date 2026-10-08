"""Reminder URL patterns (mounted at /api/v1/)."""

from django.urls import path

from apps.reminders import views

urlpatterns = [
    path("reminders/", views.RemindersView.as_view(), name="reminders"),
    path("reminders/bulk/", views.ReminderBulkView.as_view(), name="reminders-bulk"),
    path("reminders/<int:pk>/", views.ReminderItemView.as_view(), name="reminder-item"),
    path("cron/daily/", views.DailyCronView.as_view(), name="cron-daily"),
]
