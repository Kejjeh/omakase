import json

import pytest

from scripts.pipeline import enrich
from scripts.shared.geo import Area
from scripts.scoring import Scoring
from scripts.sources import GoogleSource, InfatuationSource, YelpSource


class _StubCuisine:
    """Minimal Cuisine for enrich() tests — supplies sources and specialty data inline.

    Defaults to a name with no registered Region, so enrich() derives no
    neighborhood and these stay pure unit tests that never touch the ~2.4MB
    boundary file. Geo derivation is covered below with an injected resolver.
    """

    def __init__(self, sources, specialties=None, name="stub-no-region"):
        self.name = name
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
    # No Region for this cuisine, so the hand label is left exactly as-is.
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


# --- neighborhood derivation ---
#
# The master sheet's hand-typed `neighborhood` disagreed with reality in both
# directions, so enrich() demotes it to `neighborhood_raw` and derives the real
# one from the coordinates Places returns. A stub resolver keeps these unit
# tests off the real boundary file.


def _resolver(area):
    return lambda lat, lng: area


def test_enrich_demotes_hand_label_and_derives_from_coordinates():
    # Mirrors the real Uka Omakase: hand-labelled UWS, actually on E 60th.
    restaurants = [{"name": "Uka", "neighborhood": "Manhattan (UWS)", "min_price": 56}]
    google = GoogleSource(cache={"Uka": {
        "rating": 4.9, "review_count": 2444, "google_name": "Uka Omakase",
        "lat": 40.76142, "lng": -73.96473,
        "address": "238 E 60th St", "place_id": "abc", "business_status": "OPERATIONAL",
    }})
    cuisine = _StubCuisine(sources=[google])
    area = Area(code="MN0801", name="Upper East Side-Lenox Hill-Roosevelt Island", borough="Manhattan")

    r = enrich(cuisine, restaurants, scored={}, user_state={}, resolve_area=_resolver(area))[0]

    assert r["neighborhood_raw"] == "Manhattan (UWS)"
    assert r["borough"] == "Manhattan"
    assert r["nta_name"] == "Upper East Side-Lenox Hill-Roosevelt Island"
    assert r["nta_code"] == "MN0801"
    # The untrustworthy key must not survive under its old name.
    assert "neighborhood" not in r


def test_enrich_carries_location_fields_from_google_onto_the_record():
    restaurants = [{"name": "R1", "neighborhood": "X"}]
    google = GoogleSource(cache={"R1": {
        "rating": 4.5, "review_count": 100, "google_name": "R1",
        "lat": 40.7, "lng": -73.9, "address": "1 Main St",
        "place_id": "pid", "business_status": "OPERATIONAL",
    }})
    cuisine = _StubCuisine(sources=[google])

    r = enrich(cuisine, restaurants, scored={}, user_state={}, resolve_area=_resolver(None))[0]

    assert r["lat"] == 40.7
    assert r["lng"] == -73.9
    assert r["address"] == "1 Main St"
    assert r["place_id"] == "pid"
    assert r["business_status"] == "OPERATIONAL"


def test_enrich_leaves_derived_fields_null_when_restaurant_is_outside_the_region():
    # Jersey City: real restaurant, genuinely outside the NYC boundary set. Its
    # hand label survives in neighborhood_raw rather than being invented.
    restaurants = [{"name": "Nigiri", "neighborhood": "Jersey City, NJ"}]
    google = GoogleSource(cache={"Nigiri": {
        "rating": 4.5, "review_count": 50, "lat": 40.71552, "lng": -74.0431,
    }})
    cuisine = _StubCuisine(sources=[google])

    r = enrich(cuisine, restaurants, scored={}, user_state={}, resolve_area=_resolver(None))[0]

    assert r["neighborhood_raw"] == "Jersey City, NJ"
    assert r["borough"] is None
    assert r["nta_name"] is None
    assert r["nta_code"] is None


def test_enrich_leaves_derived_fields_null_when_google_could_not_locate_it():
    restaurants = [{"name": "Masuda Omakase", "neighborhood": "Manhattan (Midtown)"}]
    cuisine = _StubCuisine(sources=[GoogleSource(cache={})])

    r = enrich(cuisine, restaurants, scored={}, user_state={}, resolve_area=_resolver(None))[0]

    assert r["neighborhood_raw"] == "Manhattan (Midtown)"
    assert r["lat"] is None
    assert r["nta_name"] is None


def test_enrich_skips_derivation_entirely_for_a_city_with_no_boundaries():
    # philly/kensington have no Region. Deriving nothing must leave their hand
    # label in place, not blank it.
    restaurants = [{"name": "R1", "neighborhood": "Fishtown"}]
    cuisine = _StubCuisine(sources=[GoogleSource(cache={})])

    r = enrich(cuisine, restaurants, scored={}, user_state={}, resolve_area=None)[0]

    assert r["neighborhood"] == "Fishtown"
    assert "neighborhood_raw" not in r
    assert "borough" not in r


def test_enrich_derives_over_a_specialty_supplied_hand_label():
    # Italian research files also carry `neighborhood`, merged after the master
    # sheet. Whichever hand label wins, it is still only a raw label.
    restaurants = [{"name": "R1", "neighborhood": "from-master"}]
    cuisine = _StubCuisine(
        sources=[GoogleSource(cache={"R1": {"rating": 4.0, "review_count": 10, "lat": 40.7, "lng": -73.9}})],
        specialties={"R1": {"neighborhood": "from-research"}},
    )
    area = Area(code="MN0803", name="Upper East Side-Yorkville", borough="Manhattan")

    r = enrich(cuisine, restaurants, scored={}, user_state={}, resolve_area=_resolver(area))[0]

    assert r["neighborhood_raw"] == "from-research"
    assert r["nta_name"] == "Upper East Side-Yorkville"


# --- closed / open ---
#
# `closed` used to conflate two things: a deliberate "this shut down" from a
# research file, and the pipeline's default False, which only meant "nobody
# said". Google's business_status can fill the second without overwriting the
# first — and must not overwrite it, because the restaurants where Google
# disagreed all turned out to have wrong Places matches.


def _google(**fields):
    base = {"rating": 4.5, "review_count": 100, "google_name": "R1", "place_id": "pid"}
    return GoogleSource(cache={"R1": {**base, **fields}})


def _enrich_one(cuisine, restaurant, trusted=True):
    return enrich(cuisine, [restaurant], scored={}, user_state={},
                  resolve_area=None, is_trusted=lambda name: trusted)[0]


def test_permanently_closed_on_google_closes_a_restaurant_nobody_had_marked():
    cuisine = _StubCuisine(sources=[_google(business_status="CLOSED_PERMANENTLY")])

    r = _enrich_one(cuisine, {"name": "R1"})

    assert r["closed"] is True
    assert r["closed_override"] is None
    assert r["temporarily_closed"] is False


def test_an_explicit_assertion_beats_google_saying_operational():
    # The real ROKI/Robataya/Sushi Yugen case: the restaurant shut, Places
    # substituted a similarly-named operating business, and its OPERATIONAL
    # status must not reopen the restaurant.
    cuisine = _StubCuisine(
        sources=[_google(business_status="OPERATIONAL")],
        specialties={"R1": {"closed": True}},
    )

    r = _enrich_one(cuisine, {"name": "R1"})

    assert r["closed"] is True
    assert r["closed_override"] is True


def test_an_explicit_assertion_of_open_beats_google_saying_closed():
    # The override has to work in both directions, or it isn't an override.
    cuisine = _StubCuisine(
        sources=[_google(business_status="CLOSED_PERMANENTLY")],
        specialties={"R1": {"closed": False}},
    )

    r = _enrich_one(cuisine, {"name": "R1"})

    assert r["closed"] is False
    assert r["closed_override"] is False


def test_an_untrusted_match_never_closes_a_restaurant():
    # The status belongs to whatever business Places actually returned.
    cuisine = _StubCuisine(sources=[_google(business_status="CLOSED_PERMANENTLY")])

    r = _enrich_one(cuisine, {"name": "R1"}, trusted=False)

    assert r["closed"] is False
    assert r["temporarily_closed"] is False


def test_temporary_closure_is_tracked_separately_from_permanent():
    cuisine = _StubCuisine(sources=[_google(business_status="CLOSED_TEMPORARILY")])

    r = _enrich_one(cuisine, {"name": "R1"})

    assert r["closed"] is False
    assert r["temporarily_closed"] is True


def test_a_restaurant_google_cannot_find_stays_open_by_default():
    cuisine = _StubCuisine(sources=[GoogleSource(cache={})])

    r = _enrich_one(cuisine, {"name": "R1"}, trusted=False)

    assert r["closed"] is False
    assert r["closed_override"] is None


def test_an_asserted_closure_survives_google_having_no_opinion():
    cuisine = _StubCuisine(
        sources=[GoogleSource(cache={})],
        specialties={"R1": {"closed": True}},
    )

    r = _enrich_one(cuisine, {"name": "R1"}, trusted=False)

    assert r["closed"] is True
