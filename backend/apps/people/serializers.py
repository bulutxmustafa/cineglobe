"""Request/response serializers for people endpoints (also drive the OpenAPI schema)."""

from rest_framework import serializers

from apps.people.credits import ROLES, SORT_MODES

MEDIA_TYPES = ["both", "movie", "tv"]


# --- Requests ---------------------------------------------------------------


class FilmographyQuerySerializer(serializers.Serializer):
    sort = serializers.ChoiceField(choices=SORT_MODES, default="newest")
    media_type = serializers.ChoiceField(choices=MEDIA_TYPES, default="both")
    role = serializers.ChoiceField(choices=ROLES, default="acting")
    lead_only = serializers.BooleanField(default=True)
    include_all = serializers.BooleanField(
        default=False, help_text="Show Self/archive/talk-show credits too."
    )


class TopTitlesRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False, trim_whitespace=True)
    person_id = serializers.IntegerField(min_value=1, required=False)
    media_type = serializers.ChoiceField(choices=MEDIA_TYPES, default="both")
    lang = serializers.ChoiceField(choices=["tr", "en"], required=False)

    def validate(self, attrs):
        if not attrs.get("name") and not attrs.get("person_id"):
            raise serializers.ValidationError("Provide 'name' or 'person_id'.")
        return attrs


# --- Responses --------------------------------------------------------------


class PersonSummarySerializer(serializers.Serializer):
    tmdb_id = serializers.IntegerField()
    name = serializers.CharField()
    known_for_department = serializers.CharField()
    profile_url = serializers.CharField()
    known_for = serializers.ListField(child=serializers.CharField())
    popularity = serializers.FloatField()


class CreditSerializer(serializers.Serializer):
    media_type = serializers.ChoiceField(choices=["movie", "tv"])
    tmdb_id = serializers.IntegerField()
    title = serializers.CharField()
    original_title = serializers.CharField()
    release_date = serializers.CharField(help_text="'' when unknown")
    year = serializers.IntegerField(allow_null=True)
    poster_url = serializers.CharField()
    vote_average = serializers.FloatField()
    vote_count = serializers.IntegerField()
    popularity = serializers.FloatField()
    characters = serializers.ListField(child=serializers.CharField())
    jobs = serializers.ListField(child=serializers.CharField())
    is_lead = serializers.BooleanField()
    episode_count = serializers.IntegerField(required=False, help_text="Series only")
    first_credit_year = serializers.IntegerField(
        required=False, allow_null=True, help_text="Series only"
    )


class TopTitleSerializer(CreditSerializer):
    reason = serializers.CharField()


class TopTitlesSectionsSerializer(serializers.Serializer):
    movies = TopTitleSerializer(many=True, required=False)
    series = TopTitleSerializer(many=True, required=False)


class TopTitlesResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["found", "ambiguous"])
    query = serializers.CharField(allow_blank=True)
    person = PersonSummarySerializer(allow_null=True)
    candidates = PersonSummarySerializer(
        many=True, help_text="Ambiguous: choices. Found: other people with the name."
    )
    media_type = serializers.CharField(required=False)
    sections = TopTitlesSectionsSerializer(required=False)


class FilmographyResponseSerializer(serializers.Serializer):
    person = serializers.DictField()
    sort = serializers.CharField()
    media_type = serializers.CharField()
    role = serializers.CharField()
    lead_only = serializers.BooleanField()
    include_all = serializers.BooleanField()
    page = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    total_results = serializers.IntegerField()
    hidden_noise_count = serializers.IntegerField()
    results = CreditSerializer(many=True)
    upcoming = CreditSerializer(many=True, help_text="'Yakında': future-dated credits")


class PersonDetailSerializer(serializers.Serializer):
    tmdb_id = serializers.IntegerField()
    name = serializers.CharField()
    biography = serializers.CharField(allow_blank=True)
    biography_language = serializers.CharField()
    biography_is_fallback = serializers.BooleanField()
    birthday = serializers.CharField(allow_null=True)
    birth_year = serializers.IntegerField(allow_null=True)
    deathday = serializers.CharField(allow_null=True)
    place_of_birth = serializers.CharField(allow_null=True)
    known_for_department = serializers.CharField()
    profile_url = serializers.CharField()
    known_for = CreditSerializer(many=True)


class PersonSearchResponseSerializer(serializers.Serializer):
    query = serializers.CharField()
    count = serializers.IntegerField()
    results = PersonSummarySerializer(many=True)
