"""Film Notebook serializers (plan §3.8)."""

from __future__ import annotations

from rest_framework import serializers

from apps.catalog.image_utils import poster_url
from apps.notebook.models import (
    MAX_NOTE_LENGTH,
    MAX_TAG_LENGTH,
    MAX_TAGS,
    NotebookEntry,
)


class NotebookEntrySerializer(serializers.ModelSerializer):
    poster_url = serializers.SerializerMethodField()

    class Meta:
        model = NotebookEntry
        fields = [
            "media_type",
            "tmdb_id",
            "status",
            "is_favorite",
            "rating_x2",
            "note",
            "tags",
            "watched_on",
            "rewatch_count",
            "progress_season",
            "progress_episode",
            "title",
            "original_title",
            "poster_url",
            "year",
            "genres",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_poster_url(self, entry: NotebookEntry) -> str:
        return poster_url(entry.poster_path or "")


class NotebookWriteSerializer(serializers.Serializer):
    """Editable fields. Strict types: a rating like 5.5 or "abc" is rejected."""

    status = serializers.ChoiceField(
        choices=NotebookEntry.Status.choices, allow_null=True, required=False
    )
    is_favorite = serializers.BooleanField(required=False)
    rating_x2 = serializers.IntegerField(
        min_value=1, max_value=10, allow_null=True, required=False
    )
    note = serializers.CharField(
        max_length=MAX_NOTE_LENGTH,
        allow_blank=True,
        required=False,
        trim_whitespace=False,
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=MAX_TAG_LENGTH, trim_whitespace=True),
        max_length=MAX_TAGS,
        required=False,
    )
    watched_on = serializers.DateField(allow_null=True, required=False)
    rewatch_count = serializers.IntegerField(min_value=0, max_value=999, required=False)
    progress_season = serializers.IntegerField(
        min_value=0, allow_null=True, required=False
    )
    progress_episode = serializers.IntegerField(
        min_value=0, allow_null=True, required=False
    )

    def validate_tags(self, value):
        return list(dict.fromkeys(tag.strip() for tag in value if tag.strip()))


class NotebookQuerySerializer(serializers.Serializer):
    SORTS = {
        "-updated_at": "-updated_at",
        "updated_at": "updated_at",
        "-rating": "-rating_x2",
        "rating": "rating_x2",
        "-watched_on": "-watched_on",
        "watched_on": "watched_on",
        "-year": "-year",
        "year": "year",
        "title": "title",
    }

    status = serializers.ChoiceField(
        choices=NotebookEntry.Status.choices, required=False
    )
    favorites = serializers.BooleanField(required=False, default=False)
    media_type = serializers.ChoiceField(choices=["movie", "tv"], required=False)
    rating_min = serializers.IntegerField(min_value=1, max_value=10, required=False)
    rating_max = serializers.IntegerField(min_value=1, max_value=10, required=False)
    tag = serializers.CharField(max_length=MAX_TAG_LENGTH, required=False)
    genre = serializers.CharField(max_length=40, required=False)
    q = serializers.CharField(max_length=100, required=False)
    sort = serializers.ChoiceField(choices=list(SORTS), default="-updated_at")


class TitleKeySerializer(serializers.Serializer):
    media_type = serializers.ChoiceField(choices=["movie", "tv"])
    tmdb_id = serializers.IntegerField(min_value=1)


class LookupSerializer(serializers.Serializer):
    items = TitleKeySerializer(many=True, max_length=100)


class MergeSerializer(serializers.Serializer):
    favorites = TitleKeySerializer(many=True, max_length=500)
