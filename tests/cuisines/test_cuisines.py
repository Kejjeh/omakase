import json

import pytest

from scripts.cuisines import ItalianCuisine, OmakaseCuisine, get_cuisine
from scripts.sources import GoogleSource, InfatuationSource, YelpSource


def test_omakase_cuisine_has_three_sources_in_canonical_order():
    c = OmakaseCuisine()
    types = [type(s) for s in c.sources]
    assert types == [GoogleSource, YelpSource, InfatuationSource]


def test_italian_cuisine_has_all_three_sources_now_that_yelp_cache_exists():
    # Initial handoff said Italian would skip Yelp (0% coverage).
    # Round-1 deep research landed 20 Yelp entries; Italian now uses the
    # YelpSource. Missing entries naturally return None, no special-casing.
    c = ItalianCuisine()
    types = [type(s) for s in c.sources]
    assert types == [GoogleSource, YelpSource, InfatuationSource]


def test_cuisine_names():
    assert OmakaseCuisine().name == "omakase"
    assert ItalianCuisine().name == "italian"


def test_registry_returns_cuisine_by_name():
    assert isinstance(get_cuisine("omakase"), OmakaseCuisine)
    assert isinstance(get_cuisine("italian"), ItalianCuisine)


def test_registry_raises_on_unknown_cuisine():
    with pytest.raises(KeyError):
        get_cuisine("french")


def test_read_restaurants_loads_canonical_json(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "restaurants.json").write_text(
        json.dumps([{"name": "R1", "neighborhood": "X"}, {"name": "R2", "neighborhood": "Y"}]),
        encoding="utf-8",
    )
    # empty caches so source construction doesn't blow up
    for n in ("ratings_cache.json", "yelp_cache.json", "infatuation_cache.json"):
        (data_dir / n).write_text("{}", encoding="utf-8")

    c = OmakaseCuisine(data_dir=data_dir, research_dir=tmp_path / "research")
    out = c.read_restaurants()

    assert out == [{"name": "R1", "neighborhood": "X"}, {"name": "R2", "neighborhood": "Y"}]


def test_read_restaurants_returns_empty_when_file_missing(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    for n in ("ratings_cache.json", "yelp_cache.json", "infatuation_cache.json"):
        (data_dir / n).write_text("{}", encoding="utf-8")

    c = ItalianCuisine(data_dir=data_dir, research_dir=tmp_path / "research")
    assert c.read_restaurants() == []


def test_load_specialties_merges_json_files_by_name(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    for n in ("ratings_cache.json", "yelp_cache.json", "infatuation_cache.json"):
        (data_dir / n).write_text("{}", encoding="utf-8")

    research = tmp_path / "research"
    research.mkdir()
    (research / "a.json").write_text(
        json.dumps([{"name": "R1", "wagyu_offered": True}]),
        encoding="utf-8",
    )
    (research / "b.json").write_text(
        json.dumps([{"name": "R1", "ayce_offered": True}, {"name": "R2", "wagyu_offered": False}]),
        encoding="utf-8",
    )

    c = OmakaseCuisine(data_dir=data_dir, research_dir=research)
    merged = c.load_specialties()

    assert merged["R1"] == {"name": "R1", "wagyu_offered": True, "ayce_offered": True}
    assert merged["R2"] == {"name": "R2", "wagyu_offered": False}


def test_italian_load_specialties_excludes_discovery_json(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    for n in ("ratings_cache.json", "yelp_cache.json", "infatuation_cache.json"):
        (data_dir / n).write_text("{}", encoding="utf-8")

    research = tmp_path / "research"
    research.mkdir()
    # discovery.json is the cuisine's seed list, not specialty enrichment
    (research / "discovery.json").write_text(
        json.dumps([{"name": "R1", "format": "trattoria"}]),
        encoding="utf-8",
    )
    (research / "specialties.json").write_text(
        json.dumps([{"name": "R1", "famous_for": "cacio e pepe"}]),
        encoding="utf-8",
    )

    c = ItalianCuisine(data_dir=data_dir, research_dir=research)
    merged = c.load_specialties()

    assert merged == {"R1": {"name": "R1", "famous_for": "cacio e pepe"}}


def test_dashboard_fields_differ_between_cuisines():
    o = OmakaseCuisine().dashboard_fields()
    i = ItalianCuisine().dashboard_fields()

    # Both share scoring + identity fields. Neighborhood ships as structured
    # parts (derived from coordinates) rather than one hand-typed string; the
    # dashboards compose the display label from them.
    common = {"name", "borough", "nta_name", "nta_code", "neighborhood_raw",
              "composite_rating", "value_score", "sources"}
    assert common <= set(o)
    assert common <= set(i)

    # Omakase-only specialty fields
    assert "wagyu_offered" in o
    assert "wagyu_offered" not in i

    # Italian-only specialty fields
    assert "pasta_program" in i
    assert "pasta_program" not in o
