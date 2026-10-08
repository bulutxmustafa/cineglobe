"""Upcoming URL patterns."""

from django.urls import path

from apps.upcoming.views import UpcomingView

urlpatterns = [path("", UpcomingView.as_view(), name="upcoming")]
