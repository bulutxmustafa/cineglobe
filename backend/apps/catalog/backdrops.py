"""Keep the title page background different from its poster.

TMDB's default backdrop is sometimes the poster's own key art, so the page would
show the same picture twice. When the default backdrop looks like the poster (similar
colour make-up AND a similar layout in some poster-shaped slice of it), the most-voted
textless backdrop with clearly different colours is used instead. The choice is cached
for a month, so it runs once per title.
"""

import io
import logging

import httpx
from django.core.cache import cache

logger = logging.getLogger(__name__)

IMAGE_BASE = "https://image.tmdb.org/t/p"
SAME_AS_POSTER = 0.75  # colour-histogram overlap at or above this = same colours
SAME_LAYOUT = 0.3  # brightness-layout correlation at or above this = same composition
DIFFERENT_ENOUGH = 0.6  # a replacement must be clearly different from the poster
MAX_CANDIDATES = 4
CACHE_SECONDS = 30 * 24 * 3600


def load_image(url: str):
    """Download a small TMDB image as an RGB Pillow image."""
    from PIL import Image  # lazy: only needed on the first visit of a title

    response = httpx.get(url, timeout=3)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGB")


def colour_histogram(image) -> list[float]:
    """A 64-bin RGB histogram of the image (sums to 1)."""
    bins = [0] * 64
    for r, g, b in image.resize((48, 48)).getdata():
        bins[(r // 64) * 16 + (g // 64) * 4 + b // 64] += 1
    total = sum(bins) or 1
    return [count / total for count in bins]


def _correlation(a: list[int], b: list[int]) -> float:
    n = len(a)
    mean_a, mean_b = sum(a) / n, sum(b) / n
    var_a = sum((x - mean_a) ** 2 for x in a) ** 0.5
    var_b = sum((y - mean_b) ** 2 for y in b) ** 0.5
    if not var_a or not var_b:
        return 0.0
    return sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b, strict=True)) / (
        var_a * var_b
    )


def layout_match(poster, backdrop) -> float:
    """How well the poster's brightness layout matches the best poster-shaped
    slice of the backdrop (1 = same composition)."""
    small = list(poster.convert("L").resize((12, 18)).getdata())
    gray = backdrop.convert("L")
    width, height = gray.size
    slice_width = int(height * 2 / 3)
    best = 0.0
    for fraction in (0, 0.25, 0.5, 0.75, 1):
        left = int((width - slice_width) * fraction)
        part = gray.crop((left, 0, left + slice_width, height)).resize((12, 18))
        best = max(best, _correlation(small, list(part.getdata())))
    return best


def similarity(a: list[float], b: list[float]) -> float:
    """Histogram intersection: 1 = identical colour make-up, 0 = nothing shared."""
    return sum(min(x, y) for x, y in zip(a, b, strict=True))


def choose_backdrop(
    client, media_type: str, tmdb_id: int, poster_path: str, backdrop_path: str
) -> str:
    """The backdrop to show: the default unless it repeats the poster artwork."""
    if not poster_path or not backdrop_path:
        return backdrop_path
    cache_key = f"backdrop:{media_type}:{tmdb_id}:{backdrop_path}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    chosen = backdrop_path
    try:
        poster_image = load_image(f"{IMAGE_BASE}/w185{poster_path}")
        default_image = load_image(f"{IMAGE_BASE}/w300{backdrop_path}")
        poster = colour_histogram(poster_image)
        same_artwork = (
            similarity(poster, colour_histogram(default_image)) >= SAME_AS_POSTER
            and layout_match(poster_image, default_image) >= SAME_LAYOUT
        )
        if same_artwork:
            images = client.get_images(media_type, tmdb_id)
            candidates = sorted(
                images.get("backdrops", []), key=lambda b: -(b.get("vote_count") or 0)
            )
            checked = 0
            for candidate in candidates:
                path = candidate.get("file_path")
                if not path or path == backdrop_path:
                    continue
                checked += 1
                if checked > MAX_CANDIDATES:
                    break
                hist = colour_histogram(load_image(f"{IMAGE_BASE}/w300{path}"))
                if similarity(poster, hist) < DIFFERENT_ENOUGH:
                    chosen = path
                    break
    except Exception as exc:  # any image or network problem: keep the default
        logger.info("Backdrop check skipped for %s/%s: %s", media_type, tmdb_id, exc)
        return backdrop_path
    cache.set(cache_key, chosen, CACHE_SECONDS)
    return chosen
