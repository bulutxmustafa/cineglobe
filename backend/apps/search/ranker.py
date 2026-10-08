"""Ranker: order candidates by rating × vote confidence × relevance.

- Rating confidence uses a Bayesian average so a 9.0 with 40 votes does not beat
  an 8.3 with 20k votes. Movies and series have different vote scales, so each
  media type has its own prior weight (plan §3.2: movie 1000, tv 300).
- genres_exclude is a hard filter, applied again here because TMDB's
  without_genres is not guaranteed and the relaxed (no-keyword) query may leak.
- Dedup key is (media_type, tmdb_id): a movie and a series sharing an ID both stay.
"""

from __future__ import annotations

from typing import Any

from apps.catalog.genre_map import get_movie_genre_ids, get_tv_genre_ids
from apps.search.schemas import SearchFilters

# Votes needed before a title's own rating outweighs the prior.
CONFIDENCE_VOTES = {"movie": 1000, "tv": 300}
PRIOR_RATING = 6.5
KEYWORD_BONUS = 0.08
GENRE_BONUS = 0.06
DEFAULT_LIMIT = 20


def bayesian_rating(rating: float, votes: int, media_type: str) -> float:
    m = CONFIDENCE_VOTES.get(media_type, CONFIDENCE_VOTES["movie"])
    votes = max(votes, 0)
    return (votes / (votes + m)) * rating + (m / (votes + m)) * PRIOR_RATING


class Ranker:
    def rank(
        self,
        candidates: list[dict[str, Any]],
        filters: SearchFilters,
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict[str, Any]]:
        excluded = {
            "movie": set(get_movie_genre_ids(filters.genres_exclude)),
            "tv": set(get_tv_genre_ids(filters.genres_exclude)),
        }
        wanted = {
            "movie": set(get_movie_genre_ids(filters.genres_include)),
            "tv": set(get_tv_genre_ids(filters.genres_include)),
        }

        best: dict[tuple[str, int], dict[str, Any]] = {}
        for item in candidates:
            media_type = item.get("media_type", "movie")
            genre_ids = set(item.get("genre_ids") or [])
            if genre_ids & excluded.get(media_type, set()):
                continue
            if (
                filters.min_rating is not None
                and item.get("vote_average", 0) < filters.min_rating
            ):
                continue

            score = self.score(item, wanted.get(media_type, set()))
            key = (media_type, item.get("tmdb_id"))
            if key not in best or score > best[key]["score"]:
                best[key] = {**item, "score": score}

        ranked = sorted(best.values(), key=lambda x: x["score"], reverse=True)
        return ranked[:limit]

    @staticmethod
    def score(item: dict[str, Any], wanted_genres: set[int]) -> float:
        media_type = item.get("media_type", "movie")
        base = (
            bayesian_rating(
                float(item.get("vote_average") or 0.0),
                int(item.get("vote_count") or 0),
                media_type,
            )
            / 10.0
        )
        bonus = KEYWORD_BONUS if item.get("matched_keywords") else 0.0
        if wanted_genres:
            overlap = len(set(item.get("genre_ids") or []) & wanted_genres)
            bonus += GENRE_BONUS * overlap / len(wanted_genres)
        return round(base + bonus, 4)
