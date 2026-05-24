import json

import pytest

from scripts.pipeline import enrich
from scripts.scoring import Scoring
from scripts.sources import GoogleSource, InfatuationSource, YelpSource


class _StubCuisine:
    """Minimal Cuisine for enrich() tests — supplies sources and specialty data inline."""

    def __init__(self, sources, specialties=None):
        self.sources = sources
        self._specialties = specialties or {}

    def load_specialties(self):
        return self._specialties


def test_enrich_merges_score_fields_onto_restaurant_record():
    restaurants = [{"name": "R1", "neighborhood": "X", "min_price": 50}]
    scored = {
        "R1": Scoring(
            composite_rating=4.5,
            sources="G+Y",
            value_score=9.0,
            rating_percentile=0.8,
            value_percentile=0.7,
        )
    }
    cuisine = _StubCuisine(sources=[
        GoogleSource(cache={}),
        YelpSource(cache={}),
        InfatuationSource(cache={}),
    ])

    enriched = enrich(cuisine, restaurants, scored, user_state={})

    r = enriched[0]
    assert r["composite_rating"] == 4.5
    assert r["adjusted_rating"] == 4.5
    assert r["sources"] == "G+Y"
    assert r["n_sources"] == 2
    assert r["value_score"] == 9.0
    # Scorer outputs 0-1; enrich scales to 0-100 for legacy compat
    assert r["rating_percentile"] == 80.0
    assert r["value_percentile"] == 70.0
    # base fields preserved
    assert r["name"] == "R1"
    assert r["neighborhood"] == "X"


def test_enrich_writes_per_source_raw_and_adjusted_fields():
    restaurants = [{"name": "R1", "min_price": 50}]
    google_cache = {"R1": {"rating": 5.0, "review_count": 200, "google_name": "R1 Google"}}
    yelp_cache = {"R1": {"yelp_rating": 4.5, "review_count": 100, "price_level": "$$$"}}
    infatuation_cache = {"R1": {"rating": 9.0}}

    cuisine = _StubCuisine(sources=[
        GoogleSource(cache=google_cache),
        YelpSource(cache=yelp_cache),
        InfatuationSource(cache=infatuation_cache),
    ])
    scoring = Scoring(composite_rating=4.5, sources="G+Y+I")
    enriched = enrich(cuisine, restaurants, scored={"R1": scoring}, user_state={})

    r = enriched[0]
    # Google raw + adjusted
    assert r["raw_rating"] == 5.0
    assert r["review_count"] == 200
    assert r["google_name"] == "R1 Google"
    assert r["google_wilson"] is not None
    # Yelp raw + adjusted
    assert r["yelp_rating"] == 4.5
    assert r["yelp_count"] == 100
    assert r["yelp_wilson"] is not None
    # Infatuation raw + adjusted
    assert r["infatuation_rating"] == 9.0
    # Rounded to 3dp by enrich's legacy-shape finalizer
    assert r["infatuation_5"] == round((9 - 1) / 9 * 4 + 1, 3)


def test_enrich_merges_free_form_specialty_fields():
    restaurants = [{"name": "R1"}]
    specialties = {"R1": {"name": "R1", "wagyu_offered": True, "famous_for": "toro"}}
    cuisine = _StubCuisine(sources=[GoogleSource(cache={})], specialties=specialties)

    enriched = enrich(cuisine, restaurants, scored={}, user_state={})

    r = enriched[0]
    assert r["wagyu_offered"] is True
    assert r["famous_for"] == "toro"


def test_enrich_preserves_user_state_fields():
    restaurants = [{"name": "R1"}]
    user_state = {"R1": {"visited": True, "friend_suggested": True, "subway_walk_min": 7, "nearest_456": "Bryant Park"}}
    cuisine = _StubCuisine(sources=[GoogleSource(cache={})])

    enriched = enrich(cuisine, restaurants, scored={}, user_state=user_state)

    r = enriched[0]
    assert r["visited"] is True
    assert r["friend_suggested"] is True
    assert r["subway_walk_min"] == 7
    assert r["nearest_456"] == "Bryant Park"


def test_enrich_handles_unscored_restaurant_gracefully():
    restaurants = [{"name": "Ghost", "neighborhood": "X"}]
    cuisine = _StubCuisine(sources=[GoogleSource(cache={})])

    enriched = enrich(cuisine, restaurants, scored={}, user_state={})

    r = enriched[0]
    assert r["name"] == "Ghost"
    # No score-derived fields written
    assert "composite_rating" not in r
    assert "value_score" not in r


def test_enrich_defaults_user_state_fields_to_falsy_when_absent():
    restaurants = [{"name": "R1"}]
    cuisine = _StubCuisine(sources=[GoogleSource(cache={})])

    enriched = enrich(cuisine, restaurants, scored={}, user_state={})

    r = enriched[0]
    # Legacy contract: these keys exist even if no user_state entry
    assert r["visited"] is False
    assert r["friend_suggested"] is False
    assert r["subway_walk_min"] is None
    assert r["nearest_456"] is None


def test_write_dashboard_data_projects_only_dashboard_fields(tmp_path):
    from scripts.pipeline import write_dashboard_data

    class _DashCuisine:
        name = "test"
        def dashboard_fields(self):
            return ["name", "composite_rating", "value_score"]

    cuisine = _DashCuisine()
    enriched = [
        {"name": "R1", "composite_rating": 4.5, "value_score": 8.0, "internal_field": "leak"},
        {"name": "R2", "composite_rating": 4.0, "value_score": None, "internal_field": "leak"},
    ]
    out_path = tmp_path / "data.json"

    write_dashboard_data(cuisine, enriched, out_path=out_path)

    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(data) == 2
    assert set(data[0].keys()) == {"name", "composite_rating", "value_score"}
    assert "internal_field" not in data[0]
    assert data[0]["name"] == "R1"
