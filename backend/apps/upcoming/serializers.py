"""Serializers for the upcoming endpoint (also drive the OpenAPI schema)."""

from rest_framework import serializers

from apps.catalog.genre_map import GENRE_MAP


class UpcomingQuerySerializer(serializers.Serializer):
    media_type = serializers.ChoiceField(
        choices=["both", "movie", "tv"], default="both"
    )
    genre = serializers.ChoiceField(choices=sorted(GENRE_MAP), required=False)
    month = serializers.RegexField(
        r"^\d{4}-(0[1-9]|1[0-2])$", required=False, help_text="YYYY-MM"
    )


class UpcomingItemSerializer(serializers.Serializer):
    media_type = serializers.ChoiceField(choices=["movie", "tv"])
    tmdb_id = serializers.IntegerField()
    title = serializers.CharField()
    original_title = serializers.CharField()
    overview = serializers.CharField()
    poster_url = serializers.CharField()
    backdrop_url = serializers.CharField()
    popularity = serializers.FloatField()
    genre_ids = serializers.ListField(child=serializers.IntegerField())
    release_date = serializers.CharField(help_text="'' when not yet announced")
    date_precision = serializers.ChoiceField(choices=["day", "unknown"])
    region = serializers.CharField(help_text="'TR' (Turkish date), 'global' or ''")
    group = serializers.ChoiceField(choices=["this_week", "this_month", "later", "tba"])
    season_number = serializers.IntegerField(
        required=False, allow_null=True, help_text="Series only"
    )


class UpcomingGroupSerializer(serializers.Serializer):
    key = serializers.ChoiceField(choices=["this_week", "this_month", "later", "tba"])
    items = UpcomingItemSerializer(many=True)


class UpcomingResponseSerializer(serializers.Serializer):
    today = serializers.DateField(help_text="Europe/Istanbul date used for grouping")
    media_type = serializers.CharField()
    page = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    total_results = serializers.IntegerField()
    results = UpcomingItemSerializer(many=True)
    groups = UpcomingGroupSerializer(many=True)
