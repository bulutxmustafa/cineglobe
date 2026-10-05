"""DRF serializers for the catalog app.

Converts Title / TVDetails / Genre / Person model instances (and raw TMDB
dicts) into JSON-serialisable structures for API responses.
Includes dual language support (Turkish and English).
"""

from rest_framework import serializers

from apps.catalog.image_utils import backdrop_url, poster_url
from apps.catalog.models import Genre, Person, Title, TVDetails


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name", "movie_tmdb_id", "tv_tmdb_id"]


class TVDetailsSerializer(serializers.ModelSerializer):
    is_binge_friendly = serializers.BooleanField(read_only=True)

    class Meta:
        model = TVDetails
        fields = [
            "number_of_seasons",
            "number_of_episodes",
            "status",
            "episode_runtime",
            "networks",
            "last_air_date",
            "in_production",
            "is_binge_friendly",
        ]


class TitleSerializer(serializers.ModelSerializer):
    """Full representation of a Title (film or TV show) used in detail views."""

    genres = GenreSerializer(many=True, read_only=True)
    tv_details = TVDetailsSerializer(read_only=True)
    poster_url = serializers.SerializerMethodField()
    backdrop_url = serializers.SerializerMethodField()
    display_title = serializers.SerializerMethodField()
    display_overview = serializers.SerializerMethodField()

    class Meta:
        model = Title
        fields = [
            "id",
            "media_type",
            "tmdb_id",
            "title",
            "title_en",
            "display_title",
            "original_title",
            "overview",
            "overview_en",
            "display_overview",
            "poster_path",
            "backdrop_path",
            "poster_url",
            "backdrop_url",
            "original_language",
            "vote_average",
            "vote_count",
            "popularity",
            "release_date",
            "first_air_date",
            "display_date",
            "genres",
            "tv_details",
            "cached_at",
        ]

    def get_poster_url(self, obj: Title) -> str:
        return poster_url(obj.poster_path)

    def get_backdrop_url(self, obj: Title) -> str:
        return backdrop_url(obj.backdrop_path)

    def get_display_title(self, obj: Title) -> str:
        lang = self.context.get("language", "tr")
        if lang.startswith("en") and obj.title_en:
            return obj.title_en
        return obj.title

    def get_display_overview(self, obj: Title) -> str:
        lang = self.context.get("language", "tr")
        if lang.startswith("en") and obj.overview_en:
            return obj.overview_en
        return obj.overview


class TitleListSerializer(serializers.ModelSerializer):
    """Compact representation of a Title used in list / search results."""

    poster_url = serializers.SerializerMethodField()
    reason = serializers.SerializerMethodField()
    display_title = serializers.SerializerMethodField()
    display_overview = serializers.SerializerMethodField()

    class Meta:
        model = Title
        fields = [
            "media_type",
            "tmdb_id",
            "title",
            "title_en",
            "display_title",
            "overview",
            "overview_en",
            "display_overview",
            "poster_url",
            "vote_average",
            "vote_count",
            "release_date",
            "first_air_date",
            "reason",
        ]

    def get_poster_url(self, obj: Title) -> str:
        return poster_url(obj.poster_path)

    def get_display_title(self, obj: Title) -> str:
        lang = self.context.get("language", "tr")
        if lang.startswith("en") and obj.title_en:
            return obj.title_en
        return obj.title

    def get_display_overview(self, obj: Title) -> str:
        lang = self.context.get("language", "tr")
        if lang.startswith("en") and obj.overview_en:
            return obj.overview_en
        return obj.overview

    def get_reason(self, obj: Title) -> str:
        """Inject per-result 'why this title?' reason if provided in context."""
        reasons = self.context.get("reasons", {})
        key = f"{obj.media_type}:{obj.tmdb_id}"
        return reasons.get(key, "")


class PersonSerializer(serializers.ModelSerializer):
    profile_url = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = ["tmdb_id", "name", "profile_path", "profile_url", "popularity"]

    def get_profile_url(self, obj: Person) -> str:
        from apps.catalog.image_utils import profile_url

        return profile_url(obj.profile_path)
