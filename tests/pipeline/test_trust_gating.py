"""An untrusted Places match's rating must not reach the Composite rating.

Trust gating protected everything derived from a Places field except the one
field that decides rank: the rating itself. "Bar Tulia" — a Naples, Florida
concept with no NYC presence — carried Tarallucci e Vino NoMad's reviews to #15
on the Italian dashboard, and "Olmo" carried OLIO E PIU's to #6. See ADR 0007.
"""
import pytest

from scripts import pipeline
from scripts.cuisines import _REGISTRY, get_cuisine
from scripts.pipeline import enrich, excluded_readings, score_step
from scripts.scoring import ScoringConfig
from scripts.shared import places
from scripts.sources import GoogleSource, InfatuationSource, YelpSource


class _StubCuisine:
    """Minimal Cuisine: sources inline, no Region, no specialty files."""

    def __init__(self, sources, name="stub-no-region"):
        self.name = name
        self.sources = sources

    def load_specialties(self):
        return {}


def _google(name="R1", *, rating=5.0, n=200, google_name=None, place_id="pid-r1", **extra):
    return GoogleSource(cache={name: {
        "rating": rating, "review_count": n,
        "google_name": google_name if google_name is not None else name,
        "place_id": place_id, **extra,
    }})


def _cuisine(google=None, yelp=None, infatuation=None, name="stub-no-region"):
    return _StubCuisine(name=name, sources=[
        google or GoogleSource(cache={}),
        YelpSource(cache=yelp or {}),
        InfatuationSource(cache=infatuation or {}),
    ])


def _blend(cuisine, rows=None):
    return score_step(cuisine, rows or [{"name": "R1", "min_price": 100}])


# --- the defect ------------------------------------------------------------


def test_a_wrong_business_rating_is_excluded_from_the_composite():
    # Places substituted a different operating business. Its 5.0 belongs to
    # that business, not to ours.
    cuisine = _cuisine(
        google=_google(google_name="Somewhere Else Entirely"),
        yelp={"R1": {"yelp_rating": 3.0, "review_count": 100}},
    )

    scored = _blend(cuisine)

    assert scored["R1"].sources == "Y"
    yelp_only = cuisine.sources[1].read("R1").value
    assert scored["R1"].composite_rating == pytest.approx(yelp_only)


def test_a_trusted_rating_is_retained_in_the_composite():
    cuisine = _cuisine(
        google=_google(google_name="R1 Sushi Bar"),  # containment: similarity 1.0
        yelp={"R1": {"yelp_rating": 3.0, "review_count": 100}},
    )

    scored = _blend(cuisine)

    assert scored["R1"].sources == "G+Y"


def test_a_colliding_match_is_excluded_from_both_restaurants():
    # Proof, not inference: one listing cannot be two restaurants, and nothing
    # says which claimant is the right one — so neither may keep the rating.
    shared = {"rating": 4.8, "review_count": 500,
              "google_name": "Shared Listing", "place_id": "same-id"}
    cuisine = _cuisine(
        google=GoogleSource(cache={"Shared Listing": dict(shared),
                                   "Shared Listing (Brooklyn)": dict(shared)}),
        yelp={"Shared Listing": {"yelp_rating": 4.0, "review_count": 50},
              "Shared Listing (Brooklyn)": {"yelp_rating": 4.0, "review_count": 50}},
    )
    rows = [{"name": "Shared Listing", "min_price": 100},
            {"name": "Shared Listing (Brooklyn)", "min_price": 100}]

    scored = score_step(cuisine, rows)

    assert scored["Shared Listing"].sources == "Y"
    assert scored["Shared Listing (Brooklyn)"].sources == "Y"


def test_a_match_with_no_place_id_is_excluded():
    # A null pin detaches the row deliberately (Masa). Whatever rating is still
    # cached against it cannot be attributed to any listing.
    cuisine = _cuisine(
        google=_google(place_id=None),
        yelp={"R1": {"yelp_rating": 3.0, "review_count": 100}},
    )

    assert _blend(cuisine)["R1"].sources == "Y"


# --- what must NOT change --------------------------------------------------


def test_remaining_sources_renormalize_over_the_trusted_ones_only():
    # Google 0.35 excluded, so Yelp 0.45 and Infatuation 0.20 renormalize to
    # 0.45/0.65 and 0.20/0.65 — exactly as they do when Google never covered
    # the restaurant. Exclusion is indistinguishable from absence to the Scorer.
    cuisine = _cuisine(
        google=_google(google_name="Somewhere Else Entirely"),
        yelp={"R1": {"yelp_rating": 4.0, "review_count": 100}},
        infatuation={"R1": {"rating": 8.0}},
    )
    y = cuisine.sources[1].read("R1").value
    i = cuisine.sources[2].read("R1").value

    scored = _blend(cuisine)

    expected = (y * 0.45 + i * 0.20) / 0.65
    assert scored["R1"].composite_rating == pytest.approx(expected)
    assert scored["R1"].sources == "Y+I"


def test_an_excluded_rating_never_becomes_a_zero():
    # The failure mode a naive gate invites: blending a 0 in place of the
    # withheld reading, which is worse than the wrong rating it replaced.
    cuisine = _cuisine(
        google=_google(rating=5.0, google_name="Somewhere Else Entirely"),
        yelp={"R1": {"yelp_rating": 4.0, "review_count": 100}},
    )

    composite = _blend(cuisine)["R1"].composite_rating

    yelp_only = cuisine.sources[1].read("R1").value
    assert composite == pytest.approx(yelp_only)
    assert composite > 1.0


def test_a_restaurant_left_with_no_trusted_reading_has_no_composite_at_all():
    # Not a zero, not a floor: absent. An unrated restaurant must not be rankable.
    cuisine = _cuisine(google=_google(google_name="Somewhere Else Entirely"))

    scored = _blend(cuisine)

    assert "R1" not in scored


def test_yelp_and_infatuation_are_not_gated_on_a_google_match():
    # Their caches are keyed by our name and filled by a human researching that
    # name. A wrong Places match is no evidence against them.
    cuisine = _cuisine(
        google=_google(google_name="Somewhere Else Entirely"),
        yelp={"R1": {"yelp_rating": 4.0, "review_count": 100}},
        infatuation={"R1": {"rating": 8.0}},
    )

    assert _blend(cuisine)["R1"].sources == "Y+I"


def test_weights_and_price_exponent_are_untouched_for_a_trusted_row():
    cuisine = _cuisine(
        google=_google(google_name="R1"),
        yelp={"R1": {"yelp_rating": 4.0, "review_count": 100}},
        infatuation={"R1": {"rating": 8.0}},
    )
    rows = [{"name": "R1", "min_price": 100}]
    g = cuisine.sources[0].read("R1").value
    y = cuisine.sources[1].read("R1").value
    i = cuisine.sources[2].read("R1").value

    scored = score_step(cuisine, rows, ScoringConfig(price_exponent=0.3))

    assert scored["R1"].composite_rating == pytest.approx(g * 0.35 + y * 0.45 + i * 0.20)
    assert scored["R1"].value_score == pytest.approx(scored["R1"].composite_rating)


# --- unavailable trust evidence --------------------------------------------


def test_no_places_match_at_all_is_reported_as_unknown_not_untrusted():
    # Masuda Omakase: operating, but runs inside another venue and has no
    # listing. There is nothing to judge, so the record must not claim a
    # verdict — and there was no reading to exclude.
    cuisine = _cuisine(google=GoogleSource(cache={}),
                       yelp={"R1": {"yelp_rating": 4.0, "review_count": 100}})
    rows = [{"name": "R1", "min_price": 100}]

    rec = enrich(cuisine, rows, _blend(cuisine), user_state={}, resolve_area=None)[0]

    assert rec["google_trusted"] is None
    assert rec["excluded_sources"] == []
    assert rec["composite_rating"] is not None


def test_a_cuisine_with_no_google_source_reports_no_verdict_and_no_exclusions():
    cuisine = _StubCuisine(sources=[YelpSource(cache={"R1": {"yelp_rating": 4.0,
                                                            "review_count": 100}})])
    rows = [{"name": "R1", "min_price": 100}]

    rec = enrich(cuisine, rows, score_step(cuisine, rows), user_state={},
                 resolve_area=None)[0]

    assert rec["google_trusted"] is None
    assert rec["excluded_sources"] == []
    assert rec["composite_rating"] is not None


def test_a_match_with_no_cached_google_name_is_treated_as_untrusted():
    # Missing evidence is not evidence of a good match. Gate conservatively.
    cuisine = _cuisine(google=_google(google_name=""),
                       yelp={"R1": {"yelp_rating": 4.0, "review_count": 100}})

    assert _blend(cuisine)["R1"].sources == "Y"


def test_a_match_with_no_rating_records_no_exclusion():
    # Nothing was withheld, so nothing is reported as withheld.
    cuisine = _cuisine(google=_google(rating=None, google_name="Somewhere Else"),
                       yelp={"R1": {"yelp_rating": 4.0, "review_count": 100}})
    rows = [{"name": "R1", "min_price": 100}]

    rec = enrich(cuisine, rows, _blend(cuisine), user_state={}, resolve_area=None)[0]

    assert rec["google_trusted"] is False
    assert rec["excluded_sources"] == []


# --- what the reader is told ------------------------------------------------


def test_the_record_names_the_excluded_source_and_why():
    cuisine = _cuisine(google=_google(google_name="Somewhere Else Entirely"),
                       yelp={"R1": {"yelp_rating": 4.0, "review_count": 100}})
    rows = [{"name": "R1", "min_price": 100}]

    rec = enrich(cuisine, rows, _blend(cuisine), user_state={}, resolve_area=None)[0]

    assert rec["google_trusted"] is False
    [excluded] = rec["excluded_sources"]
    assert excluded["source"] == "google"
    assert excluded["reason"] == places.NAME_MISMATCH
    assert "Somewhere Else Entirely" in excluded["detail"]
    assert excluded["excluded_rating"] == 5.0
    # The evidence a human needs to rule on the match stays on the record...
    assert rec["raw_rating"] == 5.0
    assert rec["google_name"] == "Somewhere Else Entirely"
    # ...but the adjusted Reading that feeds the blend is withdrawn with it, so
    # the record can never show a Google reading the Composite rating ignored.
    assert rec["google_wilson"] is None


def test_the_excel_cell_explains_the_gap_between_raw_rating_and_composite():
    cuisine = _cuisine(google=_google(google_name="Somewhere Else Entirely"),
                       yelp={"R1": {"yelp_rating": 4.0, "review_count": 100}})
    rows = [{"name": "R1", "min_price": 100}]
    rec = enrich(cuisine, rows, _blend(cuisine), user_state={}, resolve_area=None)[0]

    cell = pipeline.describe_exclusions(rec)

    assert cell.startswith("Google rating 5.0 excluded")
    assert "Somewhere Else Entirely" in cell


def test_a_trusted_row_carries_an_empty_exclusion_note():
    cuisine = _cuisine(google=_google(google_name="R1"))
    rows = [{"name": "R1", "min_price": 100}]

    rec = enrich(cuisine, rows, _blend(cuisine), user_state={}, resolve_area=None)[0]

    assert rec["google_trusted"] is True
    assert rec["excluded_sources"] == []
    assert pipeline.describe_exclusions(rec) == ""
    assert rec["google_wilson"] is not None


def test_excluded_readings_lists_only_readings_that_were_actually_withheld():
    cuisine = _cuisine(
        google=GoogleSource(cache={
            "Wrong": {"rating": 5.0, "review_count": 10,
                      "google_name": "Somewhere Else", "place_id": "p1"},
            "Right": {"rating": 4.0, "review_count": 10,
                      "google_name": "Right", "place_id": "p2"},
        }),
    )
    rows = [{"name": "Wrong"}, {"name": "Right"}, {"name": "Unmatched"}]

    assert excluded_readings(cuisine, rows) == {"Wrong": places.NAME_MISMATCH}


# --- overrides and derivation are unaffected --------------------------------


def test_a_closed_override_survives_its_google_reading_being_excluded():
    # Two separate assertions about the same wrong match: its rating is not
    # ours, and its OPERATIONAL status cannot reopen us. Neither may cancel
    # the other, and neither may touch the hand ruling. ADR 0005 + ADR 0007.
    class _WithSpecialty(_StubCuisine):
        def load_specialties(self):
            return {"R1": {"closed": True}}

    cuisine = _WithSpecialty(sources=[
        _google(google_name="Somewhere Else Entirely", business_status="OPERATIONAL"),
        YelpSource(cache={"R1": {"yelp_rating": 4.0, "review_count": 100}}),
    ])
    rows = [{"name": "R1", "min_price": 100}]

    rec = enrich(cuisine, rows, score_step(cuisine, rows), user_state={},
                 resolve_area=None)[0]

    assert rec["closed"] is True
    assert rec["closed_override"] is True
    assert rec["google_trusted"] is False
    assert rec["sources"] == "Y"


def test_an_untrusted_match_still_derives_no_closure():
    cuisine = _cuisine(google=_google(google_name="Somewhere Else Entirely",
                                      business_status="CLOSED_PERMANENTLY"))
    rows = [{"name": "R1", "min_price": 100}]

    rec = enrich(cuisine, rows, _blend(cuisine), user_state={}, resolve_area=None)[0]

    assert rec["closed"] is False
    assert rec["temporarily_closed"] is False


def test_scoring_and_enrich_agree_on_the_same_injected_trust_verdict():
    # The two steps take the same callable precisely so a record can never say
    # "Google excluded" beside a Composite rating that used it.
    cuisine = _cuisine(google=_google(google_name="R1"),
                       yelp={"R1": {"yelp_rating": 4.0, "review_count": 100}})
    rows = [{"name": "R1", "min_price": 100}]
    stub = lambda name: places.NAME_MISMATCH

    scored = score_step(cuisine, rows, trust_reason=stub)
    rec = enrich(cuisine, rows, scored, user_state={}, resolve_area=None,
                 trust_reason=stub)[0]

    assert rec["sources"] == "Y"
    assert [e["source"] for e in rec["excluded_sources"]] == ["google"]


# --- cross-cuisine regression over the committed caches ---------------------


@pytest.mark.parametrize("cuisine_name", sorted(_REGISTRY))
def test_no_cuisine_blends_an_untrusted_google_reading(cuisine_name):
    cuisine = get_cuisine(cuisine_name)
    restaurants = pipeline.read(cuisine)
    if not restaurants:
        pytest.skip(f"{cuisine_name} has no committed restaurants.json")
    reason_for = pipeline.trust_reason_resolver(cuisine, restaurants)

    scored = score_step(cuisine, restaurants)

    untrusted = [r["name"] for r in restaurants if reason_for(r["name"]) is not None]
    still_blended = [n for n in untrusted if "G" in scored.get(n, _NO).sources]
    assert still_blended == []


@pytest.mark.parametrize("cuisine_name", sorted(_REGISTRY))
def test_every_cuisine_explains_each_exclusion_it_makes(cuisine_name):
    cuisine = get_cuisine(cuisine_name)
    restaurants = pipeline.read(cuisine)
    if not restaurants:
        pytest.skip(f"{cuisine_name} has no committed restaurants.json")

    excluded = excluded_readings(cuisine, restaurants)
    enriched = enrich(cuisine, restaurants, score_step(cuisine, restaurants),
                      user_state={}, resolve_area=None)

    by_name = {r["name"]: r for r in enriched}
    for name, reason in excluded.items():
        rec = by_name[name]
        assert rec["google_trusted"] is False, name
        [note] = rec["excluded_sources"]
        assert note["reason"] == reason, name
        assert note["detail"], name
        # No row keeps an adjusted Google reading its composite did not use.
        assert rec["google_wilson"] is None, name
        assert "G" not in (rec.get("sources") or ""), name


@pytest.mark.parametrize("cuisine_name", sorted(_REGISTRY))
def test_no_cuisine_produces_a_zero_or_negative_composite(cuisine_name):
    cuisine = get_cuisine(cuisine_name)
    restaurants = pipeline.read(cuisine)
    if not restaurants:
        pytest.skip(f"{cuisine_name} has no committed restaurants.json")

    scored = score_step(cuisine, restaurants)

    assert scored, cuisine_name
    assert all(s.composite_rating >= 1.0 for s in scored.values())


class _NoSources:
    sources = ""


_NO = _NoSources()
