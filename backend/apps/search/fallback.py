"""Deterministic rule-based query parser used when the LLM is unavailable or fails.

It understands a practical subset of Turkish and English: genre words, a few
themes (mapped to English TMDB keywords), negation ("korku olmasın", "no horror"),
media type hints ("dizi", "series"), length hints and decades/years.
"""

from __future__ import annotations

import re

from apps.search.schemas import SearchFilters

# Keys are regex fragments matched at a word start, so Turkish suffixes
# ("gerilimli", "komedisi", "korkunç") are covered. Short English words end
# with \b so "war" does not match "warm".
GENRE_STEMS: dict[str, str] = {
    "gerilim": "Thriller",
    "thriller": "Thriller",
    "heyecanl": "Thriller",
    "suspense": "Thriller",
    "istihbarat": "Thriller",
    "casus": "Thriller",
    r"spy\b": "Thriller",
    "espionage": "Thriller",
    "korku": "Horror",
    "horror": "Horror",
    "scary": "Horror",
    "komedi": "Comedy",
    "komik": "Comedy",
    "güldür": "Comedy",
    "comedy": "Comedy",
    "funny": "Comedy",
    "aksiyon": "Action",
    "action": "Action",
    "silahlı": "Action",
    "çatışma": "Action",
    "macera": "Adventure",
    "adventure": "Adventure",
    "dram": "Drama",
    "drama": "Drama",
    "romanti": "Romance",
    "romance": "Romance",
    "aşk": "Romance",
    "bilim kurgu": "Science Fiction",
    "bilimkurgu": "Science Fiction",
    "sci-fi": "Science Fiction",
    "science fiction": "Science Fiction",
    "fantasti": "Fantasy",
    "fantasy": "Fantasy",
    "animasyon": "Animation",
    "animation": "Animation",
    "animated": "Animation",
    "çizgi film": "Animation",
    "belgesel": "Documentary",
    "documentar": "Documentary",
    "suç": "Crime",
    "polisiye": "Crime",
    "mafya": "Crime",
    "crime": "Crime",
    "gangster": "Crime",
    "gizem": "Mystery",
    "mystery": "Mystery",
    "dedektif": "Mystery",
    "detective": "Mystery",
    "savaş": "War",
    r"war\b": "War",
    "tarih": "History",
    "historical": "History",
    "history": "History",
    "aile": "Family",
    "family": "Family",
    "western": "Western",
    "kovboy": "Western",
    "cowboy": "Western",
    "müzikal": "Music",
    "musical": "Music",
}

# Stem → English TMDB keywords.
KEYWORD_STEMS: dict[str, list[str]] = {
    "istihbarat": ["intelligence agency", "espionage"],
    "intelligence": ["intelligence agency", "espionage"],
    "casus": ["spy", "espionage"],
    "ajan": ["spy", "secret agent"],
    r"spy\b": ["spy", "espionage"],
    "espionage": ["espionage"],
    "silahlı çatışma": ["shootout"],
    "shootout": ["shootout"],
    "gunfight": ["shootout"],
    "soygun": ["heist"],
    "heist": ["heist"],
    "zaman yolculu": ["time travel"],
    "time travel": ["time travel"],
    "zaman döngü": ["time loop"],
    "time loop": ["time loop"],
    "distopya": ["dystopia"],
    "distopik": ["dystopia"],
    "dystopi": ["dystopia"],
    "uzay": ["space"],
    r"space\b": ["space"],
    "zombi": ["zombie"],
    "zombie": ["zombie"],
    "seri katil": ["serial killer"],
    "serial killer": ["serial killer"],
    "gerçek hikaye": ["based on true story"],
    "gerçek olay": ["based on true story"],
    "true story": ["based on true story"],
    "sürpriz son": ["plot twist", "twist ending"],
    "plot twist": ["plot twist"],
    r"twist\b": ["plot twist"],
    "hayatta kalma": ["survival"],
    "survival": ["survival"],
    "yapay zeka": ["artificial intelligence (a.i.)"],
    "artificial intelligence": ["artificial intelligence (a.i.)"],
    "intikam": ["revenge"],
    "revenge": ["revenge"],
    "mahkeme": ["courtroom"],
    "courtroom": ["courtroom"],
}

MOOD_STEMS: dict[str, str] = {
    "keyif": "lighthearted",
    "eğlenceli": "lighthearted",
    "hafif": "lighthearted",
    "rahatlat": "lighthearted",
    "feel-good": "lighthearted",
    "feel good": "lighthearted",
    "lighthearted": "lighthearted",
    r"fun\b": "lighthearted",
    "yoğun": "intense",
    "gergin": "intense",
    "intense": "intense",
    "duygusal": "emotional",
    "emotional": "emotional",
    "karanlık": "dark",
    r"dark\b": "dark",
}

TV_STEMS = ("dizi", "series", r"shows?\b", "sezon", "season", "bölüm", "episode")
MOVIE_STEMS = ("film", "movie", "sinema", "cinema")

# Words that turn a clause into an exclusion ("korku olmasın", "no horror").
NEGATION_PATTERN = re.compile(
    r"\b(olmasın|içermesin|istemiyorum|istemem|hariç|değil|olmayan|içermeyen"
    r"|yok|olmadan|no|not|without|except|non)\b"
)
# Clauses: split on punctuation and contrast words; then on conjunctions into parts.
CLAUSE_SPLIT = re.compile(r"[,.;!?]|\b(?:ama|fakat|ancak|but)\b")
PART_SPLIT = re.compile(r"\b(?:ve|ile|veya|and|with|or)\b")
# A part with its own wish verb stops a later negation from spreading back to it:
# "korku ve şiddet olmasın" excludes both, "gerilim olsun ve korku olmasın" does not.
AFFIRMATIVE_PATTERN = re.compile(
    r"\b(olsun|istiyorum|isterim|içersin|want|like|love|please)\b"
)
NOT_TV = re.compile(
    r"\b(?:not a|no) (?:series|show)|\bdizi (?:olmasın|değil|istemiyorum)"
)

SHORT_EPISODE = re.compile(
    r"kısa bölüm|short episode|30 dakika|yarım saat|half[- ]hour|sitcom"
)
SHORT_GENERAL = re.compile(
    r"çok uzun olmasın|uzun olmasın|kısa|not too long|short|mini ?dizi|miniseries"
)
MINI_SERIES = re.compile(r"mini ?dizi|miniseries|limited series")
# Decades: "1990s", "2010'lar", "90'larda", "70'lerden", "80s". No space allowed
# before the suffix, so "50 sezon" is not read as the 1950s.
FULL_DECADE = re.compile(r"\b((?:19|20)\d)0(?:'|’)?(?:ler|lar|li|lı|s)\w*")
SHORT_DECADE = re.compile(r"\b([2-9])0(?:'|’)?(?:ler|lar|li|lı|s)\w*")
ENDED = re.compile(
    r"bitmiş|tamamlanmış|sona ermiş|\bended\b|\bfinished\b|\bcompleted?\b"
)
ONGOING = re.compile(r"devam eden|hala süren|ongoing|still running|currently airing")
YEAR = re.compile(r"\b(19\d{2}|20\d{2})\b")
AFTER_WORDS = re.compile(r"sonra|sonrası|after|since|newer")
BEFORE_WORDS = re.compile(r"önce|öncesi|before|older")
TURKISH_HINT = re.compile(r"[çğıöşü]|\b(bir|olsun|ama|gibi|izle|film|dizi)\b")


def _normalize(text: str) -> str:
    """Lowercase with Turkish dotted/dotless I handled correctly."""
    text = text.replace("İ", "i").replace("I", "ı")
    return " ".join(text.lower().split())


def _stem_hits(text: str, stems: dict) -> list:
    hits = []
    for stem, value in stems.items():
        if re.search(r"(?<!\w)" + stem, text):
            hits.append(value)
    return hits


def parse_query_fallback(query: str) -> SearchFilters:
    """Build SearchFilters from a query using keyword rules only (no LLM)."""
    text = _normalize(query)
    # The English pass uses plain lowercase so "I" stays "i".
    text_en = " ".join(query.lower().split())

    include: list[str] = []
    exclude: list[str] = []
    for clause in filter(None, (c.strip() for c in CLAUSE_SPLIT.split(text) if c)):
        parts = [p.strip() for p in PART_SPLIT.split(clause) if p.strip()]
        carry = False  # negation spreading back from a later part
        for part in reversed(parts):
            if NEGATION_PATTERN.search(part):
                negated = carry = True
            elif AFFIRMATIVE_PATTERN.search(part):
                negated = carry = False
            else:
                negated = carry
            (exclude if negated else include).extend(_stem_hits(part, GENRE_STEMS))

    keywords: list[str] = []
    for hit in _stem_hits(text, KEYWORD_STEMS):
        keywords.extend(hit)

    moods = _stem_hits(text, MOOD_STEMS)
    has_tv = any(re.search(r"(?<!\w)" + s, text) for s in TV_STEMS)
    if NOT_TV.search(text):
        has_tv, has_movie_hint = False, True
    else:
        has_movie_hint = False
    has_movie = has_movie_hint or any(
        re.search(r"(?<!\w)" + s, text) for s in MOVIE_STEMS
    )
    media_type = "tv" if has_tv and not has_movie else "both"
    if has_movie and not has_tv:
        media_type = "movie"

    episode_runtime_max = max_seasons = runtime_max = None
    if media_type == "tv":
        if SHORT_EPISODE.search(text):
            episode_runtime_max = 30
        if MINI_SERIES.search(text):
            max_seasons = 1
        elif SHORT_GENERAL.search(text) and not SHORT_EPISODE.search(text):
            max_seasons = 3
    elif media_type == "movie" and SHORT_GENERAL.search(text):
        runtime_max = 110

    year_from = year_to = None
    if decade := FULL_DECADE.search(text_en):
        year_from = int(decade.group(1)) * 10
        year_to = year_from + 9
    elif decade := SHORT_DECADE.search(text_en):
        year_from = 1900 + int(decade.group(1)) * 10
        year_to = year_from + 9
    elif year := YEAR.search(text):
        value = int(year.group(1))
        if AFTER_WORDS.search(text):
            year_from = value
        elif BEFORE_WORDS.search(text):
            year_to = value
        else:
            year_from = year_to = value

    status = "any"
    if ENDED.search(text):
        status = "ended"
    elif ONGOING.search(text):
        status = "ongoing"

    filters = SearchFilters(
        media_type=media_type,
        genres_include=include,
        genres_exclude=exclude,
        keywords=keywords,
        moods=moods,
        year_from=year_from,
        year_to=year_to,
        runtime_max=runtime_max,
        episode_runtime_max=episode_runtime_max,
        max_seasons=max_seasons,
        status=status,
        language_hint="tr" if TURKISH_HINT.search(text) else "en",
    )
    filters.is_meaningful = filters.has_signal()
    return filters
