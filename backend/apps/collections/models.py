"""Curated collections (plan §3.5): rule-generated lists editors can fine-tune in admin."""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.db import models
from pydantic import ValidationError as PydanticValidationError

from apps.collections.recipe import Recipe

TITLE_KEY = re.compile(r"^(movie|tv):\d+$")


def validate_title_keys(value) -> None:
    if not isinstance(value, list) or not all(
        isinstance(v, str) and TITLE_KEY.match(v) for v in value
    ):
        raise ValidationError('Use a list like ["movie:550", "tv:1396"].')


def validate_recipe(value) -> None:
    try:
        Recipe.model_validate(value)
    except PydanticValidationError as exc:
        messages = "; ".join(
            f"{'.'.join(map(str, e['loc'])) or 'recipe'}: {e['msg']}"
            for e in exc.errors()
        )
        raise ValidationError(f"Invalid recipe — {messages}") from None


class Collection(models.Model):
    class MediaType(models.TextChoices):
        MOVIE = "movie", "Movie"
        TV = "tv", "TV"
        BOTH = "both", "Both"

    slug = models.SlugField(max_length=60, unique=True)
    name_tr = models.CharField(max_length=80)
    name_en = models.CharField(max_length=80)
    description_tr = models.CharField(max_length=240, blank=True)
    description_en = models.CharField(max_length=240, blank=True)
    # Spoiler-free "why it's here" line shown on every title of this collection.
    reason_tr = models.CharField(
        max_length=160, blank=True, help_text="Spoiler içermemeli (ör. Tersköşe)."
    )
    reason_en = models.CharField(max_length=160, blank=True)
    icon = models.CharField(max_length=8, blank=True, help_text="An emoji, e.g. 🍿")
    media_type = models.CharField(
        max_length=5, choices=MediaType.choices, default=MediaType.MOVIE
    )
    recipe = models.JSONField(
        default=dict,
        validators=[validate_recipe],
        help_text="Rule the list is generated from; see apps/collections/recipe.py.",
    )
    editor_pins = models.JSONField(
        default=list,
        blank=True,
        validators=[validate_title_keys],
        help_text='Shown first, in this order: ["movie:550", "tv:1396"]',
    )
    editor_blocklist = models.JSONField(
        default=list,
        blank=True,
        validators=[validate_title_keys],
        help_text='Never shown: ["movie:550"]',
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "slug"]

    def __str__(self) -> str:
        return f"{self.icon} {self.name_tr}".strip()

    def parsed_recipe(self) -> Recipe:
        return Recipe.model_validate(self.recipe)

    def name(self, language: str) -> str:
        return self.name_en if language == "en" else self.name_tr

    def description(self, language: str) -> str:
        return self.description_en if language == "en" else self.description_tr

    def reason(self, language: str) -> str:
        return self.reason_en if language == "en" else self.reason_tr

    def summary(self, language: str) -> dict:
        return {
            "slug": self.slug,
            "name": self.name(language),
            "description": self.description(language),
            "name_tr": self.name_tr,
            "name_en": self.name_en,
            "icon": self.icon,
            "media_type": self.media_type,
        }
