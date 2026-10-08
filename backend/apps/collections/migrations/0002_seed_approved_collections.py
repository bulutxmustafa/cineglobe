"""Seed the six collections the user approved on 2026-10-08 (plan §3.5, first six rows).

The data is frozen here on purpose (migrations must not depend on code that
changes later). Editors can tune everything afterwards in the admin.
"""

from django.db import migrations

SEED = [
    {
        "slug": "never-boring",
        "icon": "🔥",
        "name_tr": "Sıkılmam Diyeceğiniz Filmler",
        "name_en": "Films You Won't Get Bored Of",
        "description_tr": "Temposu hiç düşmeyen, ekrana kilitleyen yüksek puanlı filmler.",
        "description_en": "High-rated films whose pace never drops for a second.",
        "reason_tr": "Temposu hiç düşmeyen, izleyenlerin çok sevdiği bir film.",
        "reason_en": "Relentless pacing, loved by audiences.",
        "recipe": {
            "genres": ["Action", "Thriller", "Adventure"],
            "genres_exclude": ["Documentary"],
            "runtime_max": 125,
            "min_rating": 7.0,
            "min_votes": 3000,
            "pages": 3,
        },
    },
    {
        "slug": "immersive",
        "icon": "🌌",
        "name_tr": "Sürükleyici Filmler",
        "name_en": "Immersive Films",
        "description_tr": "Atmosferi ve dünyasıyla sizi içine çeken filmler.",
        "description_en": "Films whose atmosphere and world pull you right in.",
        "reason_tr": "Güçlü atmosferi ve dünyasıyla içine çeken bir film.",
        "reason_en": "Pulls you in with its atmosphere and world-building.",
        "recipe": {
            "genres": ["Science Fiction", "Drama", "Mystery", "Fantasy"],
            "genres_exclude": ["Documentary", "Animation"],
            "keywords": [
                "dystopia",
                "survival",
                "psychological thriller",
                "post-apocalyptic future",
                "alternate reality",
                "space",
            ],
            "min_rating": 7.0,
            "min_votes": 1500,
            "pages": 3,
        },
    },
    {
        "slug": "snack-watch",
        "icon": "🍿",
        "name_tr": "Çerezlik Filmler",
        "name_en": "Easy Snack Watches",
        "description_tr": "Kafa yormadan keyifle izlenecek hafif filmler.",
        "description_en": "Light films you can enjoy without thinking too hard.",
        "reason_tr": "Kafa yormadan keyifle izlenecek hafif bir film.",
        "reason_en": "Easy, light and fun to watch.",
        "recipe": {
            "genres": ["Comedy", "Family", "Animation", "Romance"],
            "genres_exclude": ["Horror", "War", "Crime", "Thriller", "Documentary"],
            "runtime_max": 110,
            "min_rating": 6.5,
            "min_votes": 1500,
            "pages": 3,
        },
    },
    {
        "slug": "switch-off",
        "icon": "🎈",
        "name_tr": "Kafanızı Dağıtacak Filmler",
        "name_en": "Mind-Clearing Films",
        "description_tr": "Günün stresini unutturan, iyi hissettiren eğlenceli filmler.",
        "description_en": "Fun, feel-good films that wash the day's stress away.",
        "reason_tr": "Günün stresini unutturan, iyi hissettiren bir film.",
        "reason_en": "A feel-good film to wash the day away.",
        "recipe": {
            # Adventure/Drama/Sci-Fi pulled in epics like Interstellar (live check).
            "genres": ["Comedy", "Music", "Family", "Animation"],
            "genres_exclude": [
                "Horror",
                "Thriller",
                "War",
                "Crime",
                "Documentary",
                "Drama",
                "Science Fiction",
                "Action",
            ],
            "min_rating": 6.8,
            "min_votes": 1500,
            "pages": 3,
        },
    },
    {
        "slug": "start-to-finish",
        "icon": "⏱️",
        "name_tr": "Başladığı Gibi Bitecek Filmler",
        "name_en": "Starts Strong, Ends Strong",
        "description_tr": "Tek oturumda bitecek, temposu baştan sona düşmeyen kısa filmler.",
        "description_en": "Tight films you'll finish in one sitting, strong from start to end.",
        "reason_tr": "Tek oturumda biter, temposu baştan sona düşmez.",
        "reason_en": "One sitting, no slow stretches.",
        "recipe": {
            "genres_exclude": ["Documentary", "Music", "TV Movie"],
            "runtime_min": 75,
            "runtime_max": 110,
            "min_rating": 7.2,
            "min_votes": 3000,
            "pages": 3,
        },
    },
    {
        "slug": "curveball",
        "icon": "🌀",
        "name_tr": "Tersköşe Filmleri",
        "name_en": "Curveball Films",
        "description_tr": "Beklentilerinizi tersine çeviren, şaşırtan kurgular.",
        "description_en": "Films that turn your expectations upside down.",
        # Spoiler rule (plan §3.5): never hint at what the twist is.
        "reason_tr": "Sizi sonuna kadar tahminde bulunmaya zorlayan bir kurgu.",
        "reason_en": "Keeps you guessing until the very end.",
        # TMDB tags few films with twist keywords (Shutter Island has none), so the
        # keyword pool is topped up with well-known titles pinned by id only.
        "editor_pins": [
            "movie:11324",
            "movie:745",
            "movie:629",
            "movie:670",
            "movie:210577",
            "movie:1124",
            "movie:77",
            "movie:1592",
            "movie:1933",
            "movie:419430",
        ],
        "recipe": {
            "keywords": [
                "twist",
                "nonlinear timeline",
                "unreliable narrator",
                "dissociative identity disorder",
                "plot twist",
                "surprise ending",
            ],
            "genres_exclude": ["Documentary", "Animation"],
            "min_rating": 7.0,
            "min_votes": 1500,
            "pages": 3,
        },
    },
]


def seed(apps, schema_editor):
    Collection = apps.get_model("collections", "Collection")
    for order, data in enumerate(SEED, start=1):
        Collection.objects.update_or_create(
            slug=data["slug"],
            defaults={
                **data,
                "media_type": "movie",
                "sort_order": order,
                "is_active": True,
            },
        )


def unseed(apps, schema_editor):
    Collection = apps.get_model("collections", "Collection")
    Collection.objects.filter(slug__in=[d["slug"] for d in SEED]).delete()


class Migration(migrations.Migration):
    dependencies = [("collections", "0001_initial")]

    operations = [migrations.RunPython(seed, unseed)]
