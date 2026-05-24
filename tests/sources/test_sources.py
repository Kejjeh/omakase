import math

import pytest

from scripts.scoring import AdjustedReading
from scripts.sources import GoogleSource, InfatuationSource, YelpSource


def test_yelp_source_returns_wilson_lower_bound():
    cache = {"R1": {"yelp_rating": 4.5, "review_count": 100}}
    src = YelpSource(cache=cache)

    reading = src.read("R1")

    # Wilson lower bound for rating=4.5, n=100, max=5, z=1.96
    z = 1.96
    p = (4.5 - 1.0) / 4.0
    n = 100
    den = 1 + z * z / n
    center = p + z * z / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    expected = (center - spread) / den * 4.0 + 1.0

    assert isinstance(reading, AdjustedReading)
    assert reading.value == pytest.approx(expected, abs=1e-6)
    assert reading.n == 100


def _wilson(rating, n, max_val=5.0, z=1.96):
    p = (rating - 1.0) / (max_val - 1.0)
    den = 1 + z * z / n
    center = p + z * z / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (center - spread) / den * (max_val - 1.0) + 1.0


def test_google_source_applies_bias_correction_then_wilson():
    cache = {"R1": {"rating": 5.0, "review_count": 200}}
    src = GoogleSource(cache=cache)

    reading = src.read("R1")

    # Bias correction 0.97 applied to raw before Wilson
    expected = _wilson(5.0 * 0.97, 200)
    assert reading.value == pytest.approx(expected, abs=1e-6)
    assert reading.n == 200


def test_yelp_source_does_not_apply_bias_correction():
    cache = {"R1": {"yelp_rating": 5.0, "review_count": 200}}
    src = YelpSource(cache=cache)

    reading = src.read("R1")

    expected = _wilson(5.0, 200)
    assert reading.value == pytest.approx(expected, abs=1e-6)


def test_infatuation_source_rescales_one_to_ten_into_one_to_five():
    cache = {"R1": {"rating": 9.0}}
    src = InfatuationSource(cache=cache)

    reading = src.read("R1")

    # (9 - 1) / 9 * 4 + 1 = 32/9 + 1
    assert reading.value == pytest.approx(32 / 9 + 1, abs=1e-9)


def test_missing_restaurant_returns_none():
    g = GoogleSource(cache={})
    y = YelpSource(cache={})
    i = InfatuationSource(cache={})

    assert g.read("Ghost") is None
    assert y.read("Ghost") is None
    assert i.read("Ghost") is None


def test_zero_review_count_returns_none_for_wilson_sources():
    g = GoogleSource(cache={"R1": {"rating": 4.5, "review_count": 0}})
    y = YelpSource(cache={"R1": {"yelp_rating": 4.5, "review_count": 0}})

    assert g.read("R1") is None
    assert y.read("R1") is None


def test_infatuation_does_not_require_review_count():
    # Infatuation has no n; just a curated 1-10 rating
    src = InfatuationSource(cache={"R1": {"rating": 8.0}})

    reading = src.read("R1")

    assert reading is not None
    assert reading.value == pytest.approx((8 - 1) / 9 * 4 + 1)


def test_yelp_refresh_raises_pointing_at_prompt_file():
    src = YelpSource(cache={})
    with pytest.raises(NotImplementedError, match="Yelp_Research_Prompt"):
        src.refresh([{"name": "R1"}])


def test_entry_returns_raw_cache_dict():
    cache = {"R1": {"yelp_rating": 4.0, "review_count": 50, "price_level": "$$"}}
    src = YelpSource(cache=cache)
    assert src.entry("R1") == {"yelp_rating": 4.0, "review_count": 50, "price_level": "$$"}
    assert src.entry("Ghost") is None


def test_cache_loads_from_path_at_construction(tmp_path):
    import json as _json

    cache_file = tmp_path / "yelp.json"
    cache_file.write_text(
        _json.dumps({"R1": {"yelp_rating": 4.0, "review_count": 50}}),
        encoding="utf-8",
    )
    src = YelpSource(cache_path=str(cache_file))

    # Mutate the file after construction; read() must use the in-memory copy.
    cache_file.write_text(_json.dumps({}), encoding="utf-8")

    reading = src.read("R1")
    assert reading is not None
    assert reading.n == 50
