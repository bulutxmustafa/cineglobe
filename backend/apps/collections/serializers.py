"""Serializers for collection endpoints (also drive the OpenAPI schema)."""

from rest_framework import serializers


class CollectionSummarySerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    name_tr = serializers.CharField()
    name_en = serializers.CharField()
    icon = serializers.CharField()
    media_type = serializers.ChoiceField(choices=["movie", "tv", "both"])


class CollectionListResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    collections = CollectionSummarySerializer(many=True)


class CollectionItemSerializer(serializers.Serializer):
    media_type = serializers.ChoiceField(choices=["movie", "tv"])
    tmdb_id = serializers.IntegerField()
    title = serializers.CharField()
    display_title = serializers.CharField()
    original_title = serializers.CharField()
    overview = serializers.CharField()
    poster_url = serializers.CharField()
    backdrop_url = serializers.CharField()
    vote_average = serializers.FloatField()
    vote_count = serializers.IntegerField()
    popularity = serializers.FloatField()
    release_date = serializers.CharField()
    genre_ids = serializers.ListField(child=serializers.IntegerField())
    reason = serializers.CharField(help_text="Spoiler-free line set by the editor")
    pinned = serializers.BooleanField()


class CollectionDetailResponseSerializer(serializers.Serializer):
    collection = CollectionSummarySerializer()
    media_type = serializers.CharField()
    page = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    total_results = serializers.IntegerField()
    results = CollectionItemSerializer(many=True)


class RandomPickResponseSerializer(serializers.Serializer):
    collection = CollectionSummarySerializer()
    pick = CollectionItemSerializer(allow_null=True)


class CollectionQuerySerializer(serializers.Serializer):
    media_type = serializers.ChoiceField(
        choices=["both", "movie", "tv"], default="both"
    )


class RandomQuerySerializer(CollectionQuerySerializer):
    exclude = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        help_text="Comma-separated recent picks to avoid, e.g. movie:550,tv:1396",
    )
