from rest_framework import serializers

from apps.reminders.models import CHANNELS, Reminder


class ReminderSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField(read_only=True, allow_null=True)

    class Meta:
        model = Reminder
        fields = [
            "id",
            "media_type",
            "tmdb_id",
            "title",
            "season_number",
            "remind_on",
            "channels",
            "status",
            "last_known_release_date",
            "release_date_changed_at",
            "due_date",
            "created_at",
        ]
        read_only_fields = fields


class ReminderCreateSerializer(serializers.Serializer):
    media_type = serializers.ChoiceField(choices=["movie", "tv"])
    tmdb_id = serializers.IntegerField(min_value=1)
    remind_on = serializers.ChoiceField(
        choices=Reminder.RemindOn.choices, default=Reminder.RemindOn.RELEASE_DAY
    )
    channels = serializers.ListField(
        child=serializers.ChoiceField(choices=CHANNELS),
        default=lambda: ["in_app"],
        allow_empty=False,
        max_length=len(CHANNELS),
    )


class ReminderBulkSerializer(serializers.Serializer):
    """Guest 'Remind me' clicks saved in the browser, sent once after sign-in."""

    items = ReminderCreateSerializer(many=True, max_length=50)
