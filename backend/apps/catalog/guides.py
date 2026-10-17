"""Search-friendly film and series guides (landing pages for common searches).

Each guide answers a phrase people type into Google ("en iyi gerilim filmleri",
"bu akşam ne izlesem") with a ranked list from TMDB discover and a short,
unique intro. The web app renders them at /{lang}/liste/{slug}.
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Guide:
    slug: str
    media_type: str  # "movie" or "tv"
    title_tr: str
    title_en: str
    intro_tr: str
    intro_en: str
    params: dict = field(default_factory=dict)
    recent_years: int = 0  # >0: only titles released within this many years

    def discover_params(self, today: date | None = None) -> dict:
        params = {"include_adult": "false", **self.params}
        if self.recent_years:
            start = (today or date.today()).year - self.recent_years
            key = (
                "primary_release_date.gte"
                if self.media_type == "movie"
                else "first_air_date.gte"
            )
            params[key] = f"{start}-01-01"
        return params

    def title(self, lang: str) -> str:
        return self.title_en if lang.startswith("en") else self.title_tr

    def intro(self, lang: str) -> str:
        return self.intro_en if lang.startswith("en") else self.intro_tr


TOP_RATED = {"sort_by": "vote_average.desc", "vote_count.gte": 1500}
TOP_RATED_TV = {"sort_by": "vote_average.desc", "vote_count.gte": 400}

GUIDES: tuple[Guide, ...] = (
    Guide(
        slug="bu-aksam-ne-izlesem",
        media_type="movie",
        title_tr="Bu akşam ne izlesem? Son yılların sevilen filmleri",
        title_en="What to watch tonight? Loved films of recent years",
        intro_tr=(
            "Karar veremiyorsan buradan başla: son birkaç yılın hem çok izlenen hem de "
            "izleyicilerden yüksek puan alan filmleri. Liste her gün güncellenir."
        ),
        intro_en=(
            "Can't decide? Start here: films from the last few years that are both "
            "widely watched and highly rated by viewers. Updated daily."
        ),
        params={
            "sort_by": "popularity.desc",
            "vote_average.gte": 7,
            "vote_count.gte": 500,
        },
        recent_years=3,
    ),
    Guide(
        slug="en-iyi-gerilim-filmleri",
        media_type="movie",
        title_tr="En iyi gerilim filmleri",
        title_en="Best thriller films",
        intro_tr=(
            "Nefesini tutturan, sonuna kadar bırakmayan gerilimler. İzleyici puanı en "
            "yüksek, binlerce kişinin oy verdiği filmler arasından seçildi."
        ),
        intro_en=(
            "Thrillers that keep you holding your breath to the end, picked from the "
            "highest-rated films with thousands of viewer votes."
        ),
        params={**TOP_RATED, "with_genres": "53"},
    ),
    Guide(
        slug="en-iyi-komedi-filmleri",
        media_type="movie",
        title_tr="En iyi komedi filmleri",
        title_en="Best comedy films",
        intro_tr=(
            "Kahkahayı garantileyen, tekrar tekrar izlenen komediler. Kafanı dağıtmak "
            "istediğin akşamlar için izleyicilerin en sevdikleri."
        ),
        intro_en=(
            "Comedies that guarantee a laugh and hold up to rewatching: the audience "
            "favourites for evenings when you want to switch off."
        ),
        params={**TOP_RATED, "with_genres": "35", "without_genres": "80,53,27"},
    ),
    Guide(
        slug="en-iyi-korku-filmleri",
        media_type="movie",
        title_tr="En iyi korku filmleri",
        title_en="Best horror films",
        intro_tr=(
            "Işıkları kapatıp izlenecek korku filmleri: klasikleşmiş başyapıtlardan "
            "yeni dönemin konuşulan yapımlarına, puanı en yüksek olanlar."
        ),
        intro_en=(
            "Horror films to watch with the lights off, from classic masterpieces to "
            "the most talked-about new releases, ranked by viewer score."
        ),
        params={**TOP_RATED, "with_genres": "27", "vote_count.gte": 1000},
    ),
    Guide(
        slug="en-iyi-bilim-kurgu-filmleri",
        media_type="movie",
        title_tr="En iyi bilim kurgu filmleri",
        title_en="Best science fiction films",
        intro_tr=(
            "Zamanda yolculuk, uzay, yapay zekâ ve başka dünyalar. Hem düşündüren hem "
            "sürükleyen, izleyici puanı en yüksek bilim kurgu filmleri."
        ),
        intro_en=(
            "Time travel, space, artificial intelligence and other worlds: the "
            "highest-rated science fiction films that thrill and make you think."
        ),
        params={**TOP_RATED, "with_genres": "878", "without_genres": "16"},
    ),
    Guide(
        slug="aileyle-izlenecek-filmler",
        media_type="movie",
        title_tr="Aileyle izlenecek filmler",
        title_en="Films to watch with the family",
        intro_tr=(
            "Her yaştan izleyicinin keyif alacağı, aile boyu izlenebilecek filmler. "
            "Hafta sonu akşamları için en sevilenler."
        ),
        intro_en=(
            "Films that viewers of every age enjoy together: the best-loved picks for "
            "a family movie night."
        ),
        params={**TOP_RATED, "with_genres": "10751", "vote_count.gte": 1000},
    ),
    Guide(
        slug="en-iyi-animasyon-filmleri",
        media_type="movie",
        title_tr="En iyi animasyon filmleri",
        title_en="Best animated films",
        intro_tr=(
            "Sadece çocuklar için değil: hikâyesi ve görselliğiyle herkesi etkileyen, "
            "izleyici puanı en yüksek animasyon filmleri."
        ),
        intro_en=(
            "Not just for kids: animated films whose stories and visuals win everyone "
            "over, ranked by viewer score."
        ),
        params={**TOP_RATED, "with_genres": "16", "vote_count.gte": 1000},
    ),
    Guide(
        slug="en-iyi-dram-filmleri",
        media_type="movie",
        title_tr="En iyi dram filmleri",
        title_en="Best drama films",
        intro_tr=(
            "İz bırakan hikâyeler ve unutulmaz performanslar. Sinema tarihinin en çok "
            "sevilen dram filmleri, izleyici puanına göre."
        ),
        intro_en=(
            "Stories that stay with you and unforgettable performances: the best-loved "
            "drama films in cinema history, by viewer score."
        ),
        params={**TOP_RATED, "with_genres": "18", "vote_count.gte": 3000},
    ),
    Guide(
        slug="en-iyi-suc-dizileri",
        media_type="tv",
        title_tr="En iyi suç ve dedektif dizileri",
        title_en="Best crime and detective series",
        intro_tr=(
            "Çözülmeyi bekleyen davalar, zeki dedektifler ve sürükleyici suç "
            "hikâyeleri. Bölüm bölüm bağlanacağın, en yüksek puanlı diziler."
        ),
        intro_en=(
            "Cases waiting to be solved, brilliant detectives and gripping crime "
            "stories: the highest-rated series you will binge episode after episode."
        ),
        params={**TOP_RATED_TV, "with_genres": "80", "without_genres": "16"},
    ),
    Guide(
        slug="en-iyi-komedi-dizileri",
        media_type="tv",
        title_tr="En iyi komedi dizileri",
        title_en="Best comedy series",
        intro_tr=(
            "Kısa bölümlü, hafif ve güldüren diziler. Günün yorgunluğunu atmak için "
            "izleyicilerin en çok sevdiği komediler."
        ),
        intro_en=(
            "Light, funny series with short episodes: the comedies viewers love most "
            "for winding down after a long day."
        ),
        params={
            "sort_by": "vote_count.desc",
            "vote_average.gte": 7.5,
            "with_genres": "35",
            "without_genres": "16,10762",
        },
    ),
)

GUIDES_BY_SLUG = {guide.slug: guide for guide in GUIDES}
