"""Request/response serializers for the natural-language search endpoint."""

from rest_framework import serializers

MAX_QUERY_LENGTH = 300


class SearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField(
        max_length=MAX_QUERY_LENGTH, allow_blank=True, trim_whitespace=True
    )
    media_type = serializers.ChoiceField(
        choices=["movie", "tv", "both"], default="both"
    )
    lang = serializers.ChoiceField(choices=["tr", "en"], required=False)


class SearchResultSerializer(serializers.Serializer):
    media_type = serializers.CharField()
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
    score = serializers.FloatField()
    reason = serializers.CharField()


class SearchResponseSerializer(serializers.Serializer):
    query = serializers.CharField()
    lang = serializers.CharField()
    media_type = serializers.CharField()
    parser = serializers.ChoiceField(choices=["gemini", "anthropic", "classic"])
    ai_status = serializers.ChoiceField(
        choices=["ok", "quota_exceeded", "budget_exceeded", "fallback"]
    )
    filters = serializers.DictField()
    count = serializers.IntegerField()
    results = SearchResultSerializer(many=True)
    took_ms = serializers.IntegerField()
    cached = serializers.BooleanField()
