"""The dashboard's headline stats, exercised as JavaScript.

`updateStats` is the one piece of dashboard logic that can invent a claim:
it names a single restaurant as "Best Value". Since ADR 0007 a row can be
unrated, and an unrated row has no value score to compare - so the reduce
that picks the winner has to be told what a candidate is.

There is no JS test runner in this repo and the brief forbids adding one, so
these tests lift the function out of the shipped HTML and run it under the
node already on PATH (see jsharness.py). That keeps the assertion on the file
that is actually served, not on a copy that can drift.
"""

import json

import pytest
from jsharness import DASHBOARDS, extract, run_node, source


def run_update_stats(cuisine: str, rows: list[dict]) -> dict:
    """Return {element id: textContent} after updateStats() runs over `rows`."""
    src = source(cuisine)
    harness = f"""
const filtered = {json.dumps(rows)};
const out = {{}};
const document = {{
  getElementById: (id) => ({{ set textContent(v) {{ out[id] = String(v); }} }}),
}};
{extract(src, "function setRatingNote(")}
{extract(src, "function updateStats()")}
updateStats();
console.log(JSON.stringify(out));
"""
    return run_node(harness)


def rated(name, rating, value, price, n_sources=2):
    return {
        "name": name,
        "composite_rating": rating,
        "value_score": value,
        "min_price": price,
        "n_sources": n_sources,
    }


def unrated(name, price=25):
    # Exactly the shape enrich() writes for a row whose only Reading was
    # withheld: no composite, no value score, no sources left.
    return {
        "name": name,
        "composite_rating": None,
        "value_score": None,
        "min_price": price,
        "n_sources": 0,
    }


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_all_unrated_has_no_best_value(cuisine):
    """The reported defect: an unrated row was named Best Value."""
    out = run_update_stats(cuisine, [unrated("Bar Tulia"), unrated("Olmo", 40)])
    assert out["stat-best-value"] == "-"
    assert out["stat-avg-rating"] == "-"
    assert out["stat-count"] == "2"


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_unrated_row_never_beats_a_rated_one(cuisine):
    out = run_update_stats(
        cuisine,
        [
            unrated("Untrusted Cheap Spot", 10),
            rated("Measured Deal", 4.4, 12.0, 30),
            rated("Measured Splurge", 4.6, 3.0, 300),
        ],
    )
    assert out["stat-best-value"] == "Measured Deal"


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_priceless_row_is_not_a_candidate(cuisine):
    """A rated row with no price gets no value score, so it cannot win."""
    out = run_update_stats(
        cuisine,
        [
            rated("No Price Listed", 4.9, None, None),
            rated("Priced And Scored", 4.1, 9.5, 45),
        ],
    )
    assert out["stat-best-value"] == "Priced And Scored"
    assert out["stat-avg-price"] == "$45"


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_corroboration_still_beats_a_single_source_bargain(cuisine):
    """Pre-existing behavior this fix must not undo (the AYCE BBQ case)."""
    out = run_update_stats(
        cuisine,
        [
            rated("One Source Bargain", 4.8, 99.0, 15, n_sources=1),
            rated("Corroborated Deal", 4.3, 11.0, 35, n_sources=3),
        ],
    )
    assert out["stat-best-value"] == "Corroborated Deal"


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_single_source_wins_when_nothing_is_corroborated(cuisine):
    """The corroboration preference is a preference, not a second gate."""
    out = run_update_stats(
        cuisine,
        [
            rated("Lone Cheap", 4.0, 20.0, 18, n_sources=1),
            rated("Lone Pricey", 4.2, 2.0, 200, n_sources=1),
            unrated("No Rating At All"),
        ],
    )
    assert out["stat-best-value"] == "Lone Cheap"


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_empty_filter_reports_nothing(cuisine):
    out = run_update_stats(cuisine, [])
    assert out["stat-count"] == "0"
    assert out["stat-best-value"] == "-"


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_average_rating_ignores_unrated_rows(cuisine):
    out = run_update_stats(
        cuisine,
        [rated("A", 4.0, 5.0, 40), rated("B", 4.5, 6.0, 40), unrated("C", 40)],
    )
    assert out["stat-avg-rating"] == "4.25"


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_no_known_price_is_not_an_average_of_zero(cuisine):
    """"Avg Price $0" read as free; these restaurants just have no price on file."""
    out = run_update_stats(
        cuisine,
        [rated("Unlisted A", 4.0, None, None), rated("Unlisted B", 4.2, None, None)],
    )
    assert out["stat-avg-price"] == "-"


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_note_says_how_many_rows_the_average_covers(cuisine):
    """The count includes withheld rows (ADR 0007); the average cannot."""
    out = run_update_stats(cuisine, [rated("A", 4.0, 5.0, 40), unrated("B", 40)])
    assert out["stat-count"] == "2"
    assert out["stat-rating-note"] == "over 1 of 2 rated"


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_no_note_when_every_row_is_rated(cuisine):
    out = run_update_stats(
        cuisine, [rated("A", 4.0, 5.0, 40), rated("B", 4.2, 6.0, 40)]
    )
    assert out["stat-rating-note"] == ""
