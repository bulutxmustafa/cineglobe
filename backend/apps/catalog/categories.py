"""Curated & mood-based categories catalog.

Provides handcrafted film and TV categories such as 'Tersköşe', 'Sürükleyici',
'Çerezlik', 'Kafanızı Dağıtacak', 'Başladığı Gibi Bitecek' etc.
Supports bilingual presentation (Turkish & English).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CuratedCategory:
    slug: str
    title_tr: str
    title_en: str
    description_tr: str
    description_en: str
    icon: str
    media_type: str  # 'movie', 'tv', 'both'
    tmdb_params_movie: dict[str, Any]
    tmdb_params_tv: dict[str, Any]

    def to_dict(self, language: str = "tr") -> dict[str, Any]:
        """Serialize category metadata based on preferred language."""
        is_en = language.lower().startswith("en")
        return {
            "slug": self.slug,
            "title": self.title_en if is_en else self.title_tr,
            "description": self.description_en if is_en else self.description_tr,
            "title_tr": self.title_tr,
            "title_en": self.title_en,
            "description_tr": self.description_tr,
            "description_en": self.description_en,
            "icon": self.icon,
            "media_type": self.media_type,
        }


CURATED_CATEGORIES: list[CuratedCategory] = [
    CuratedCategory(
        slug="sikilmam-diyeceginiz",
        title_tr="Sıkılmam Diyeceğiniz Yapımlar",
        title_en="Never Boring / Can't Look Away",
        description_tr="Temposu bir an bile düşmeyen, ekrana kitleyen yüksek tempolu başyapıtlar.",
        description_en="High-octane masterclasses where the pace never drops for a single second.",
        icon="🔥",
        media_type="both",
        tmdb_params_movie={
            "with_genres": "28,53",  # Action, Thriller
            "vote_average.gte": 7.3,
            "vote_count.gte": 1200,
            "sort_by": "popularity.desc",
        },
        tmdb_params_tv={
            "with_genres": "10759,80",  # Action & Adventure, Crime
            "vote_average.gte": 7.8,
            "vote_count.gte": 400,
            "sort_by": "popularity.desc",
        },
    ),
    CuratedCategory(
        slug="surukleyici",
        title_tr="Sürükleyici & Nefes Kesen",
        title_en="Edge of Your Seat Thrillers",
        description_tr="Soluksuz izletecek, merak duygusunu zirvede tutan gerilim ve aksiyonlar.",
        description_en="Nail-biting thrillers and mysteries designed to keep your adrenaline pumping.",
        icon="⚡",
        media_type="both",
        tmdb_params_movie={
            "with_genres": "53,9648",  # Thriller, Mystery
            "vote_average.gte": 7.0,
            "vote_count.gte": 800,
            "sort_by": "vote_average.desc",
        },
        tmdb_params_tv={
            "with_genres": "9648,80",  # Mystery, Crime
            "vote_average.gte": 7.5,
            "vote_count.gte": 300,
            "sort_by": "vote_average.desc",
        },
    ),
    CuratedCategory(
        slug="cerezlik",
        title_tr="Çerezlik & Akıcı Eğlence",
        title_en="Popcorn Entertainment",
        description_tr="Yorulmadan keyifle izleyebileceğiniz, hafif ve eğlenceli yapımlar.",
        description_en="Lighthearted, easy-to-digest watches perfect for relaxing with friends or solo.",
        icon="🍿",
        media_type="both",
        tmdb_params_movie={
            "with_genres": "35,12",  # Comedy, Adventure
            "vote_average.gte": 6.7,
            "vote_count.gte": 700,
            "sort_by": "popularity.desc",
        },
        tmdb_params_tv={
            "with_genres": "35,10759",  # Comedy, Action & Adventure
            "vote_average.gte": 7.2,
            "vote_count.gte": 250,
            "sort_by": "popularity.desc",
        },
    ),
    CuratedCategory(
        slug="kafanizi-dagitacak",
        title_tr="Kafanızı Dağıtacak Kaçış Yapımları",
        title_en="Feel-Good Escapism",
        description_tr="Günün stresini unutturan, pozitif hissettiren ve kahkaha attıran favoriler.",
        description_en="Uplifting, feel-good stories designed to melt away everyday stress.",
        icon="🎈",
        media_type="both",
        tmdb_params_movie={
            "with_genres": "35,10751",  # Comedy, Family
            "vote_average.gte": 7.0,
            "vote_count.gte": 500,
            "sort_by": "popularity.desc",
        },
        tmdb_params_tv={
            "with_genres": "35,10762",  # Comedy, Kids
            "vote_average.gte": 7.5,
            "vote_count.gte": 200,
            "sort_by": "popularity.desc",
        },
    ),
    CuratedCategory(
        slug="basladigi-gibi-bitecek",
        title_tr="Başladığı Gibi Bitecek Kısa & Tempolu",
        title_en="Brisk & Fast-Paced (Short Runtime)",
        description_tr="Zamanı kısıtlı olanlar için su gibi akıp giden, kompakt süreli yapımlar.",
        description_en="Lean and fast-paced gems with shorter runtimes that never overstay their welcome.",
        icon="⏱️",
        media_type="movie",
        tmdb_params_movie={
            "with_runtime.lte": 105,  # <= 105 minutes
            "vote_average.gte": 7.1,
            "vote_count.gte": 600,
            "sort_by": "popularity.desc",
        },
        tmdb_params_tv={},
    ),
    CuratedCategory(
        slug="terskose",
        title_tr="Tersköşe / Şaşırtıcı Sonlar",
        title_en="Mind-Bending Plot Twists",
        description_tr="Tahminlerinizi altüst eden, finaliyle şok yaratan akıl oyunları.",
        description_en="Brilliantly constructed mysteries with unforgettable twists that flip the story upside down.",
        icon="🤯",
        media_type="both",
        tmdb_params_movie={
            "with_genres": "9648,53",  # Mystery, Thriller
            "vote_average.gte": 7.4,
            "vote_count.gte": 1500,
            "sort_by": "vote_average.desc",
        },
        tmdb_params_tv={
            "with_genres": "9648,18",  # Mystery, Drama
            "vote_average.gte": 7.8,
            "vote_count.gte": 400,
            "sort_by": "vote_average.desc",
        },
    ),
    CuratedCategory(
        slug="adrenalin-patlamasi",
        title_tr="Adrenalin Patlaması",
        title_en="Pure Adrenaline Rush",
        description_tr="Dövüş sahneleri, kovalamacalar ve aralıksız aksiyon fırtınası.",
        description_en="Non-stop stunts, breathtaking car chases, and explosive fight choreography.",
        icon="💣",
        media_type="both",
        tmdb_params_movie={
            "with_genres": "28",  # Action
            "vote_average.gte": 7.0,
            "vote_count.gte": 1000,
            "sort_by": "popularity.desc",
        },
        tmdb_params_tv={
            "with_genres": "10759",  # Action & Adventure
            "vote_average.gte": 7.5,
            "vote_count.gte": 300,
            "sort_by": "popularity.desc",
        },
    ),
    CuratedCategory(
        slug="beyin-yakan-gizemler",
        title_tr="Beyin Yakan Gizemler & Bilim Kurgu",
        title_en="Cerebral Sci-Fi & Mind Games",
        description_tr="Zaman yolculuğu, kuantum olasılıkları ve felsefi derinlik içeren zihin açıcılar.",
        description_en="Time loops, alternate dimensions, and high-concept philosophical puzzles.",
        icon="🌀",
        media_type="both",
        tmdb_params_movie={
            "with_genres": "878,9648",  # Sci-Fi, Mystery
            "vote_average.gte": 7.3,
            "vote_count.gte": 1000,
            "sort_by": "vote_average.desc",
        },
        tmdb_params_tv={
            "with_genres": "10765,9648",  # Sci-Fi & Fantasy, Mystery
            "vote_average.gte": 7.8,
            "vote_count.gte": 350,
            "sort_by": "vote_average.desc",
        },
    ),
    CuratedCategory(
        slug="goz-yasartanlar",
        title_tr="Duygu Yüklü & Göz Yaşartanlar",
        title_en="Tearjerkers & Emotional Journeys",
        description_tr="Mendilleri hazırlayın; kalbe dokunan, derin duygular yaşatan dramlar.",
        description_en="Deeply moving and beautifully painful dramas guaranteed to touch your soul.",
        icon="🥺",
        media_type="both",
        tmdb_params_movie={
            "with_genres": "18,10749",  # Drama, Romance
            "vote_average.gte": 7.5,
            "vote_count.gte": 800,
            "sort_by": "vote_average.desc",
        },
        tmdb_params_tv={
            "with_genres": "18",  # Drama
            "vote_average.gte": 8.0,
            "vote_count.gte": 300,
            "sort_by": "vote_average.desc",
        },
    ),
    CuratedCategory(
        slug="kisa-ve-vurucu-diziler",
        title_tr="Kısa ve Vurucu Mini Diziler",
        title_en="Bingeable Limited & Mini Series",
        description_tr="Hafta sonu bir oturuşta bitirebileceğiniz, tek sezonluk güçlü mini diziler.",
        description_en="Compelling single-season limited series you can effortlessly devour in a single weekend.",
        icon="📺",
        media_type="tv",
        tmdb_params_movie={},
        tmdb_params_tv={
            "with_genres": "18,80,9648",  # Drama, Crime, Mystery
            "vote_average.gte": 7.8,
            "vote_count.gte": 300,
            "sort_by": "popularity.desc",
        },
    ),
]

_CATEGORY_LOOKUP = {c.slug: c for c in CURATED_CATEGORIES}


def get_curated_category(slug: str) -> CuratedCategory | None:
    """Find category by slug."""
    return _CATEGORY_LOOKUP.get(slug)


def get_all_curated_categories(language: str = "tr") -> list[dict[str, Any]]:
    """Return all categories serialized for API response."""
    return [c.to_dict(language=language) for c in CURATED_CATEGORIES]
