from __future__ import annotations

import json
import os
from pathlib import Path

from scripts.sources import GoogleSource, InfatuationSource, YelpSource


class ItalianCuisine:
    name = "italian"

    def __init__(self, data_dir: str | os.PathLike | None = None, research_dir: str | os.PathLike | None = None):
        root = Path(__file__).resolve().parents[1] / "data" / self.name
        self._data_dir = Path(data_dir) if data_dir else root
        research_root = (
            Path(__file__).resolve().parents[2] / "research_input" / self.name
        )
        self._research_dir = Path(research_dir) if research_dir else research_root
        self.sources = [
            GoogleSource(cache_path=str(self._data_dir / "ratings_cache.json")),
            YelpSource(cache_path=str(self._data_dir / "yelp_cache.json")),
            InfatuationSource(cache_path=str(self._data_dir / "infatuation_cache.json")),
        ]

    def read_restaurants(self) -> list[dict]:
        path = self._data_dir / "restaurants.json"
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def load_specialties(self) -> dict[str, dict]:
        merged: dict[str, dict] = {}
        if not self._research_dir.exists():
            return merged
        for f in sorted(self._research_dir.glob("*.json")):
            if f.name == "discovery.json":
                continue  # the cuisine's seed list, not specialty enrichment
            data = json.loads(f.read_text(encoding="utf-8"))
            records = data if isinstance(data, list) else []
            for r in records:
                if isinstance(r, dict) and "name" in r:
                    merged.setdefault(r["name"], {}).update(r)
        return merged

    def dashboard_fields(self) -> list[str]:
        return [
            "name", "neighborhood", "format", "price_str", "min_price",
            "vibe", "address",
            "raw_rating", "google_wilson", "review_count",
            "yelp_rating", "yelp_wilson", "yelp_count",
            "infatuation_rating", "infatuation_5",
            "composite_rating", "n_sources", "sources",
            "visited", "friend_suggested",
            "subway_walk_min", "nearest_456",
            "value_score", "rating_percentile", "value_percentile",
            "subtype", "famous_for", "tasting_format", "price_level",
            "typical_dinner_pp", "pasta_program", "pizza_program",
            "vintage", "reservation", "michelin",
            "closed", "caveat",
        ]
