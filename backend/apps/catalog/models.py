"""Catalog Django models: Title, Genre, Person, TVDetails.

CRITICAL: TMDB assigns the same integer ID to both movies and TV shows,
so the composite key (media_type, tmdb_id) is used as the unique identifier
in every model, cache key, and URL throughout the system.
"""

from django.db import models


class Genre(models.Model):
    """A film or TV genre as defined by TMDB.

    Each genre tracks separate IDs for movies and TV shows because TMDB
    uses different ID spaces for the two media types (e.g. logical genre
    'Action' → movie_genre_id=28, tv_genre_id=10759).
    """

    MOVIE = "movie"
    TV = "tv"
    MEDIA_TYPE_CHOICES = [
        (MOVIE, "Movie"),
        (TV, "TV Show"),
    ]

    name = models.CharField(max_length=100)
    movie_tmdb_id = models.IntegerField(null=True, blank=True)
    tv_tmdb_id = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Person(models.Model):
    """An actor, director, or crew member as returned by TMDB person endpoints."""

    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    profile_path = models.CharField(max_length=500, blank=True, default="")
    popularity = models.FloatField(default=0.0)

    class Meta:
        ordering = ["-popularity"]

    def __str__(self) -> str:
        return self.name


class Title(models.Model):
    """A film or TV show unified under a single model.

    WARNING: TMDB movie IDs and TV IDs can collide numerically.
    Always use (media_type, tmdb_id) together as the logical primary key.
    The unique_together constraint enforces this at the DB level.
    """

    MOVIE = "movie"
    TV = "tv"
    MEDIA_TYPE_CHOICES = [
        (MOVIE, "Movie"),
        (TV, "TV Show"),
    ]

    # --- Core Identity ---
    media_type = models.CharField(max_length=5, choices=MEDIA_TYPE_CHOICES)
    tmdb_id = models.IntegerField()

    # --- Common Fields ---
    title = models.CharField(
        max_length=500
    )  # movie title or TV show name (Turkish/default)
    title_en = models.CharField(max_length=500, blank=True, default="")  # English title
    original_title = models.CharField(max_length=500, blank=True, default="")
    overview = models.TextField(blank=True, default="")  # Turkish/default overview
    overview_en = models.TextField(blank=True, default="")  # English overview
    poster_path = models.CharField(max_length=500, blank=True, default="")
    backdrop_path = models.CharField(max_length=500, blank=True, default="")
    original_language = models.CharField(max_length=10, blank=True, default="")

    # --- Ratings ---
    vote_average = models.FloatField(default=0.0)
    vote_count = models.IntegerField(default=0)
    popularity = models.FloatField(default=0.0)

    # --- Release / Air Dates ---
    release_date = models.DateField(null=True, blank=True)  # movie
    first_air_date = models.DateField(null=True, blank=True)  # TV

    # --- Genres ---
    genres = models.ManyToManyField(Genre, blank=True, related_name="titles")

    # --- Housekeeping ---
    cached_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("media_type", "tmdb_id")]
        ordering = ["-popularity"]
        indexes = [
            models.Index(fields=["media_type", "tmdb_id"]),
            models.Index(fields=["-vote_average"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.media_type})"

    @property
    def display_date(self) -> str:
        """Return the relevant date string depending on media_type."""
        date = (
            self.release_date if self.media_type == self.MOVIE else self.first_air_date
        )
        return str(date) if date else ""


class TVDetails(models.Model):
    """Extra metadata specific to TV shows, linked one-to-one with a Title (media_type='tv')."""

    STATUS_ONGOING = "ongoing"
    STATUS_ENDED = "ended"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_ONGOING, "Ongoing"),
        (STATUS_ENDED, "Ended"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    title = models.OneToOneField(
        Title,
        on_delete=models.CASCADE,
        related_name="tv_details",
        limit_choices_to={"media_type": Title.TV},
    )

    number_of_seasons = models.IntegerField(default=0)
    number_of_episodes = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ONGOING,
    )
    episode_runtime = models.IntegerField(
        null=True, blank=True, help_text="Average episode runtime in minutes"
    )
    networks = models.JSONField(default=list, blank=True)
    last_air_date = models.DateField(null=True, blank=True)
    in_production = models.BooleanField(default=False)

    @property
    def is_binge_friendly(self) -> bool:
        """Return True when the show has ended and is fully available for binging."""
        return self.status == self.STATUS_ENDED

    def __str__(self) -> str:
        return f"TVDetails({self.title.title})"
