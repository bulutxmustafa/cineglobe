from django.contrib import admin

from apps.reminders.models import Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "media_type",
        "tmdb_id",
        "title",
        "last_known_release_date",
        "remind_on",
        "status",
    )
    list_filter = ("status", "media_type", "remind_on")
    search_fields = ("title", "user__username")
    raw_id_fields = ("user",)
