from __future__ import annotations

import json
import math
from typing import Protocol

from scripts.scoring import AdjustedReading


WILSON_Z = 1.96
GOOGLE_BIAS_CORRECTION = 0.97
RATING_MAX = 5.0


class RatingSource(Protocol):
    name: str

    def read(self, restaurant_name: str) -> AdjustedReading | None: ...

    def refresh(self, restaurants: list[dict]) -> None: ...


def _wilson_lower_bound(rating: float, n: int) -> float:
    p = (rating - 1.0) / (RATING_MAX - 1.0)
    z = WILSON_Z
    den = 1 + z * z / n
    center = p + z * z / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    lower = (center - spread) / den
    return lower * (RATING_MAX - 1.0) + 1.0


def _load_cache(cache_path: str | None, cache: dict | None) -> dict:
    if cache is not None:
        return cache
    if cache_path is None:
        return {}
    with open(cache_path, encoding="utf-8") as f:
        return json.load(f)


class _BaseSource:
    def __init__(self, *, cache_path: str | None = None, cache: dict | None = None):
        self._cache = _load_cache(cache_path, cache)

    def entry(self, restaurant_name: str) -> dict | None:
        return self._cache.get(restaurant_name)

    def entries(self) -> dict:
        """Whole cache, for checks that span restaurants (e.g. duplicate place_id)."""
        return self._cache


class GoogleSource(_BaseSource):
    name = "google"

    def read(self, restaurant_name: str) -> AdjustedReading | None:
        entry = self._cache.get(restaurant_name)
        if not entry:
            return None
        rating = entry.get("rating")
        n = entry.get("review_count") or 0
        if rating is None or n == 0:
            return None
        corrected = rating * GOOGLE_BIAS_CORRECTION
        return AdjustedReading(_wilson_lower_bound(corrected, n), n)

    def refresh(self, restaurants: list[dict]) -> None:
        raise NotImplementedError("Google refresh not yet lifted from step2_fetch_ratings.py")


class YelpSource(_BaseSource):
    name = "yelp"

    def read(self, restaurant_name: str) -> AdjustedReading | None:
        entry = self._cache.get(restaurant_name)
        if not entry:
            return None
        rating = entry.get("yelp_rating")
        n = entry.get("review_count") or 0
        if rating is None or n == 0:
            return None
        return AdjustedReading(_wilson_lower_bound(rating, n), n)

    def refresh(self, restaurants: list[dict]) -> None:
        raise NotImplementedError(
            "Yelp refresh is manual. See Yelp_Research_Prompt.md "
            "(and Yelp_Research_Prompt_italian.md for the Italian cuisine)."
        )


class InfatuationSource(_BaseSource):
    name = "infatuation"

    def read(self, restaurant_name: str) -> AdjustedReading | None:
        entry = self._cache.get(restaurant_name)
        if not entry:
            return None
        rating = entry.get("rating")
        if rating is None:
            return None
        rescaled = (rating - 1.0) / 9.0 * 4.0 + 1.0
        return AdjustedReading(rescaled, None)

    def refresh(self, restaurants: list[dict]) -> None:
        raise NotImplementedError(
            "Infatuation refresh not yet lifted from step2b_fetch_infatuation.py"
        )
