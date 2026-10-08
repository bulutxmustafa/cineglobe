"""Editors manage collections here without code changes (plan Faz 4B)."""

from django.contrib import admin

from apps.collections.models import Collection


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = (
        "sort_order",
        "icon",
        "name_tr",
        "slug",
        "media_type",
        "is_active",
        "updated_at",
    )
    list_display_links = ("name_tr",)
    list_editable = ("sort_order", "is_active")
    list_filter = ("is_active", "media_type")
    search_fields = ("slug", "name_tr", "name_en")
    prepopulated_fields = {"slug": ("name_en",)}
    fieldsets = (
        (None, {"fields": ("slug", "icon", "media_type", "is_active", "sort_order")}),
        ("Türkçe", {"fields": ("name_tr", "description_tr", "reason_tr")}),
        ("English", {"fields": ("name_en", "description_en", "reason_en")}),
        (
            "Kural ve kürasyon",
            {
                "fields": ("recipe", "editor_pins", "editor_blocklist"),
                "description": (
                    "Kaydedince liste bir sonraki istekte yeniden üretilir (önbellek "
                    "kendiliğinden yenilenir). Tarif alanları: genres, genres_exclude, "
                    "keywords, runtime_min/max, min_rating, min_votes, vote_count_max, "
                    "year_from/to, episode_runtime_max, status, sort_by "
                    "(rating | popularity | newest), pages (1-5)."
                ),
            },
        ),
    )
