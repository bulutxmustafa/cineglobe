"""DRF Serializers for people/actor endpoints."""

from rest_framework import serializers

from apps.catalog.image_utils import poster_url, profile_url


class PersonDetailSerializer(serializers.Serializer):
    """Full detail of an actor or director."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    biography = serializers.CharField(allow_blank=True)
    birthday = serializers.CharField(allow_null=True, required=False)
    deathday = serializers.CharField(allow_null=True, required=False)
    place_of_birth = serializers.CharField(allow_null=True, required=False)
    profile_url = serializers.SerializerMethodField()
    popularity = serializers.FloatField(default=0.0)
    known_for_department = serializers.CharField(allow_blank=True, default="")

    def get_profile_url(self, obj) -> str:
        return profile_url(obj.get("profile_path", ""))


class PersonCreditItemSerializer(serializers.Serializer):
    """Single movie or TV show credit in an actor's filmography."""

    tmdb_id = serializers.IntegerField(source="id")
    title = serializers.SerializerMethodField()
    display_title = serializers.SerializerMethodField()
    media_type = serializers.CharField()
    character = serializers.CharField(allow_blank=True, default="")
    job = serializers.CharField(allow_blank=True, default="")
    department = serializers.CharField(allow_blank=True, default="")
    release_date = serializers.SerializerMethodField()
    poster_url = serializers.SerializerMethodField()
    vote_average = serializers.FloatField(default=0.0)
    vote_count = serializers.IntegerField(default=0)
    popularity = serializers.FloatField(default=0.0)
    episode_count = serializers.IntegerField(required=False, default=0)

    def get_title(self, obj) -> str:
        return obj.get("title") or obj.get("name", "")

    def get_display_title(self, obj) -> str:
        return self.get_title(obj)

    def get_release_date(self, obj) -> str:
        return obj.get("release_date") or obj.get("first_air_date") or ""

    def get_poster_url(self, obj) -> str:
        return poster_url(obj.get("poster_path", ""))
