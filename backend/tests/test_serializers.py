"""Tests for catalog serializers."""

import pytest
from apps.catalog.models import Genre, Person, Title, TVDetails
from apps.catalog.serializers import (
    GenreSerializer,
    PersonSerializer,
    TitleListSerializer,
    TitleSerializer,
    TVDetailsSerializer,
)


@pytest.mark.django_db
def test_title_and_list_serializer_display_and_reasons():
    """Verify TitleSerializer and TitleListSerializer with dual language and reasons."""
    title = Title.objects.create(
        media_type="movie",
        tmdb_id=1,
        title="Yıldızlararası",
        title_en="Interstellar",
        overview="Solucan deliği...",
        overview_en="A wormhole...",
        poster_path="/poster.jpg",
        backdrop_path="/backdrop.jpg",
    )

    # TR Context
    serializer_tr = TitleSerializer(title, context={"language": "tr"})
    assert serializer_tr.data["display_title"] == "Yıldızlararası"
    assert serializer_tr.data["display_overview"] == "Solucan deliği..."

    # EN Context
    serializer_en = TitleSerializer(title, context={"language": "en"})
    assert serializer_en.data["display_title"] == "Interstellar"
    assert serializer_en.data["display_overview"] == "A wormhole..."

    # TitleListSerializer with reason
    reasons = {"movie:1": "Because you love Christopher Nolan"}
    list_serializer = TitleListSerializer(
        title, context={"language": "en", "reasons": reasons}
    )
    assert list_serializer.data["reason"] == "Because you love Christopher Nolan"
    assert list_serializer.data["display_title"] == "Interstellar"


@pytest.mark.django_db
def test_genre_and_tv_details_and_person_serializer():
    """Verify GenreSerializer, TVDetailsSerializer, and PersonSerializer."""
    genre = Genre.objects.create(name="Sci-Fi", movie_tmdb_id=878, tv_tmdb_id=10765)
    genre_data = GenreSerializer(genre).data
    assert genre_data["name"] == "Sci-Fi"
    assert genre_data["movie_tmdb_id"] == 878

    tv_title = Title.objects.create(
        media_type="tv",
        tmdb_id=2,
        title="Dark",
    )
    tv_details = TVDetails.objects.create(
        title=tv_title,
        number_of_seasons=3,
        number_of_episodes=26,
        status="ended",
    )
    tv_data = TVDetailsSerializer(tv_details).data
    assert tv_data["number_of_seasons"] == 3
    assert tv_data["is_binge_friendly"] is True

    person = Person.objects.create(
        tmdb_id=3,
        name="Cillian Murphy",
        profile_path="/cillian.jpg",
        popularity=85.0,
    )
    person_data = PersonSerializer(person).data
    assert person_data["name"] == "Cillian Murphy"
    assert "https://image.tmdb.org" in person_data["profile_url"]
