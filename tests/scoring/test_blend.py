import math

import pytest

from scripts.scoring import AdjustedReading, ScoringConfig, score


def test_three_source_weighted_blend():
    restaurants = [{"name": "R1", "price": 50}]
    adjusted = {
        "google": {"R1": AdjustedReading(value=4.0, n=100)},
        "yelp": {"R1": AdjustedReading(value=4.5, n=200)},
        "infatuation": {"R1": AdjustedReading(value=3.5, n=1)},
    }

    out = score(restaurants, adjusted, ScoringConfig())

    assert out["R1"].composite_rating == pytest.approx(4.125)
    assert out["R1"].sources == "G+Y+I"


@pytest.mark.parametrize(
    ("adjusted", "expected_composite", "expected_sources"),
    [
        pytest.param(
            {
                "google": {"R1": AdjustedReading(value=4.0, n=100)},
                "yelp": {"R1": AdjustedReading(value=4.5, n=200)},
            },
            (4.0 * 0.35 + 4.5 * 0.45) / (0.35 + 0.45),
            "G+Y",
            id="google-yelp",
        ),
        pytest.param(
            {
                "google": {"R1": AdjustedReading(value=4.0, n=100)},
                "infatuation": {"R1": AdjustedReading(value=3.5, n=1)},
            },
            (4.0 * 0.35 + 3.5 * 0.20) / (0.35 + 0.20),
            "G+I",
            id="google-infatuation",
        ),
        pytest.param(
            {
                "google": {"R1": None},
                "yelp": {"R1": AdjustedReading(value=4.5, n=200)},
                "infatuation": {"R1": AdjustedReading(value=3.5, n=1)},
            },
            (4.5 * 0.45 + 3.5 * 0.20) / (0.45 + 0.20),
            "Y+I",
            id="none-reading-is-missing",
        ),
        pytest.param(
            {"yelp": {"R1": AdjustedReading(value=4.5, n=200)}},
            4.5,
            "Y",
            id="single-source",
        ),
    ],
)
def test_missing_sources_renormalize_weights_and_sources(
    adjusted, expected_composite, expected_sources
):
    restaurants = [{"name": "R1", "price": 50}]

    out = score(restaurants, adjusted, ScoringConfig())

    assert out["R1"].composite_rating == pytest.approx(expected_composite)
    assert out["R1"].sources == expected_sources


@pytest.mark.parametrize(
    ("price", "expected_value"),
    [
        pytest.param(50, 4.125 * (100 / 50), id="valid-price"),
        pytest.param(0, None, id="zero-price"),
        pytest.param(-10, None, id="negative-price"),
        pytest.param(None, None, id="none-price"),
    ],
)
def test_value_score_requires_valid_price(price, expected_value):
    restaurants = [{"name": "R1", "price": price}]
    adjusted = {
        "google": {"R1": AdjustedReading(value=4.0, n=100)},
        "yelp": {"R1": AdjustedReading(value=4.5, n=200)},
        "infatuation": {"R1": AdjustedReading(value=3.5, n=1)},
    }
    config = ScoringConfig(price_exponent=1.0)

    out = score(restaurants, adjusted, config)

    if expected_value is None:
        assert out["R1"].value_score is None
    else:
        assert out["R1"].value_score == pytest.approx(expected_value)


def test_percentile_cohorts_rating_all_scored_value_priced_only():
    restaurants = [
        {"name": "R1", "price": 50},
        {"name": "R2", "price": 20},
        {"name": "R3", "price": 100},
        {"name": "R4", "price": None},  # scored but no value
    ]
    adjusted = {
        "google": {
            "R1": AdjustedReading(4.0, 100),
            "R2": AdjustedReading(3.0, 100),
            "R3": AdjustedReading(4.5, 100),
            "R4": AdjustedReading(4.0, 100),
        },
        "yelp": {
            "R1": AdjustedReading(4.5, 100),
            "R2": AdjustedReading(3.5, 100),
            "R3": AdjustedReading(4.8, 100),
            "R4": AdjustedReading(4.2, 100),
        },
        "infatuation": {
            "R1": AdjustedReading(3.5, 100),
            "R2": AdjustedReading(3.0, 100),
            "R3": AdjustedReading(4.0, 100),
            "R4": AdjustedReading(3.8, 100),
        },
    }
    config = ScoringConfig(price_exponent=1.0)

    out = score(restaurants, adjusted, config)

    # Composites: R3=4.535, R1=4.125, R4=4.05, R2=3.225
    assert out["R3"].rating_percentile == pytest.approx(1.0)
    assert out["R1"].rating_percentile == pytest.approx(2 / 3)
    assert out["R4"].rating_percentile == pytest.approx(1 / 3)
    assert out["R2"].rating_percentile == pytest.approx(0.0)

    # Value cohort excludes R4. R2=16.125, R1=8.25, R3=4.535
    assert out["R2"].value_percentile == pytest.approx(1.0)
    assert out["R1"].value_percentile == pytest.approx(0.5)
    assert out["R3"].value_percentile == pytest.approx(0.0)
    assert out["R4"].value_percentile is None


def test_percentile_single_scored_restaurant_is_one():
    restaurants = [{"name": "R1", "price": 50}]
    adjusted = {"yelp": {"R1": AdjustedReading(4.5, 100)}}
    config = ScoringConfig(price_exponent=1.0)

    out = score(restaurants, adjusted, config)

    assert out["R1"].rating_percentile == pytest.approx(1.0)
    assert out["R1"].value_percentile == pytest.approx(1.0)


def test_percentile_ties_get_average_rank():
    restaurants = [
        {"name": "A", "price": 50},
        {"name": "B", "price": 50},
        {"name": "C", "price": 50},
    ]
    adjusted = {
        "yelp": {
            "A": AdjustedReading(4.0, 100),
            "B": AdjustedReading(4.0, 100),
            "C": AdjustedReading(5.0, 100),
        },
    }
    config = ScoringConfig(price_exponent=1.0)

    out = score(restaurants, adjusted, config)

    # Ranks: A,B tied for 1-2 -> avg 1.5; C rank 3
    # percentile = (avg_rank - 1) / (N - 1)
    assert out["C"].rating_percentile == pytest.approx(1.0)
    assert out["A"].rating_percentile == pytest.approx(0.25)
    assert out["B"].rating_percentile == pytest.approx(0.25)


def test_auto_exponent_fallback_when_cohort_under_min():
    # Only 3 priced+scored restaurants -> below AUTO_PRICE_EXPONENT_MIN_PAIRS (5)
    restaurants = [
        {"name": "R1", "price": 50},
        {"name": "R2", "price": 80},
        {"name": "R3", "price": 100},
    ]
    adjusted = {
        "yelp": {
            "R1": AdjustedReading(4.0, 100),
            "R2": AdjustedReading(4.2, 100),
            "R3": AdjustedReading(4.5, 100),
        }
    }
    config = ScoringConfig(price_exponent="auto")

    out = score(restaurants, adjusted, config)

    # Fallback exponent = 0.3
    assert out["R1"].value_score == pytest.approx(4.0 * (100 / 50) ** 0.3)
    assert out["R2"].value_score == pytest.approx(4.2 * (100 / 80) ** 0.3)
    assert out["R3"].value_score == pytest.approx(4.5 * (100 / 100) ** 0.3)


def test_auto_exponent_fits_log_log_regression():
    # Construct composites = price**0.4 (so log_r = 0.4 * log_p) -> fitted exp ~= 0.4
    prices = [20, 40, 60, 80, 100, 150]
    composites = [p ** 0.4 for p in prices]
    restaurants = [{"name": f"R{i}", "price": p} for i, p in enumerate(prices)]
    adjusted = {
        "yelp": {f"R{i}": AdjustedReading(c, 100) for i, c in enumerate(composites)}
    }
    config = ScoringConfig(price_exponent="auto")

    out = score(restaurants, adjusted, config)

    # Reverse-derive the exponent the impl used, from any one value_score.
    # value = composite * (100/price)**exp  ->  exp = log(value/composite) / log(100/price)
    r0 = out["R0"]
    derived_exp = math.log(r0.value_score / composites[0]) / math.log(100 / prices[0])
    assert derived_exp == pytest.approx(0.4, abs=1e-9)


def test_auto_exponent_clamped_to_max():
    # Steep slope: composites = price**1.0 -> beta=1.0 -> clamp to 0.6
    prices = [20, 40, 60, 80, 100, 150]
    composites = [p ** 1.0 for p in prices]
    restaurants = [{"name": f"R{i}", "price": p} for i, p in enumerate(prices)]
    adjusted = {
        "yelp": {f"R{i}": AdjustedReading(c, 100) for i, c in enumerate(composites)}
    }
    config = ScoringConfig(price_exponent="auto")

    out = score(restaurants, adjusted, config)

    r0 = out["R0"]
    derived_exp = math.log(r0.value_score / composites[0]) / math.log(100 / prices[0])
    assert derived_exp == pytest.approx(0.6, abs=1e-9)


def test_auto_exponent_clamped_to_min():
    # Shallow slope: composites = price**0.02 -> beta=0.02 -> clamp to 0.1
    prices = [20, 40, 60, 80, 100, 150]
    composites = [p ** 0.02 for p in prices]
    restaurants = [{"name": f"R{i}", "price": p} for i, p in enumerate(prices)]
    adjusted = {
        "yelp": {f"R{i}": AdjustedReading(c, 100) for i, c in enumerate(composites)}
    }
    config = ScoringConfig(price_exponent="auto")

    out = score(restaurants, adjusted, config)

    r0 = out["R0"]
    derived_exp = math.log(r0.value_score / composites[0]) / math.log(100 / prices[0])
    assert derived_exp == pytest.approx(0.1, abs=1e-9)


def test_value_score_when_price_key_absent():
    restaurants = [{"name": "R1"}]
    adjusted = {"yelp": {"R1": AdjustedReading(value=4.5, n=200)}}
    config = ScoringConfig(price_exponent=1.0)

    out = score(restaurants, adjusted, config)

    assert out["R1"].value_score is None


def test_zero_source_restaurant_omitted():
    restaurants = [
        {"name": "R1", "price": 50},
        {"name": "Ghost", "price": 40},
    ]
    adjusted = {
        "google": {"R1": AdjustedReading(value=4.0, n=100)},
        "yelp": {"R1": AdjustedReading(value=4.5, n=200), "Ghost": None},
        "infatuation": {"R1": AdjustedReading(value=3.5, n=1)},
    }

    out = score(restaurants, adjusted, ScoringConfig())

    assert "Ghost" not in out
    assert "R1" in out


def test_unknown_name_in_adjusted_ignored():
    restaurants = [{"name": "R1", "price": 50}]
    adjusted = {
        "google": {
            "R1": AdjustedReading(value=4.0, n=100),
            "Stranger": AdjustedReading(value=5.0, n=999),
        },
        "yelp": {"R1": AdjustedReading(value=4.5, n=200)},
        "infatuation": {"R1": AdjustedReading(value=3.5, n=1)},
    }

    out = score(restaurants, adjusted, ScoringConfig())

    assert set(out.keys()) == {"R1"}
