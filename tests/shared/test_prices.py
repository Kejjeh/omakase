"""`min_price` is hand-curated, so it needs guarding against rot.

The two price fields are not interchangeable (see CONTEXT.md, "Price point"):
`min_price` is the representative omakase the Value score reads, `price_str` is
a display string. They disagree on 26 omakase rows *by design* — `min_price`
often names a later tier than the cheapest one listed, or a figure `price_str`
has not caught up with. So a disagreement is not a defect and must not be
"fixed" by re-deriving `min_price` from `price_str`: doing that would move the
value percentile of every row in the cuisine.

What *is* a defect is a `min_price` that matches no tier a multi-tier
`price_str` lists. That is not a judgement call about which tier counts, it is
a figure with no provenance — which is how Sushi Seki sat at 120 against a
listed `$60 / $150` until the real tiers turned out to be $120/$150/$180.
"""
import json
import re

import pytest

from scripts.shared import paths

CUISINES = paths.CUISINES

# A multi-tier price_str whose min_price matches none of its tiers, where the
# mismatch is known and cannot currently be resolved.
UNRESOLVED_PRICE_DRIFT = {
    # Permanently closed (Google CLOSED_PERMANENTLY, Yelp "Kintsugi Omakase
    # (CLOSED)"), and its menu was re-tiered at least once before it shut:
    # press lists $95/$155/$195 and later $65/$95/$125/$175, neither holding a
    # $90. No live source can settle it, and the row is closed so the Value
    # score never reaches a dashboard.
    ("omakase", "Kintsugi"),
}


def _rows(cuisine):
    path = paths.restaurants_json(cuisine)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _tiers(price_str):
    """Every dollar figure listed in a price_str, in order."""
    if price_str is None:
        return []
    return [int(n) for n in re.findall(r"\d+", str(price_str))]


@pytest.mark.parametrize("cuisine", CUISINES)
def test_min_price_is_a_plausible_per_person_figure(cuisine):
    # A stray 0, or a total mistaken for a per-person price, silently distorts
    # the whole cuisine's value ranking rather than failing anything.
    priced = [r for r in _rows(cuisine) if r.get("min_price") is not None]
    if not priced:
        pytest.skip(f"{cuisine} carries no price data")
    for r in priced:
        price = r["min_price"]
        assert isinstance(price, int), f"{cuisine}/{r['name']}: min_price is {type(price).__name__}, not int"
        assert 10 <= price <= 2000, f"{cuisine}/{r['name']}: implausible min_price {price}"


@pytest.mark.parametrize("cuisine", CUISINES)
def test_a_multi_tier_price_str_lists_its_min_price(cuisine):
    # Which tier min_price names is a judgement call; naming none of them is a
    # figure nobody can source.
    offenders = []
    for r in _rows(cuisine):
        price = r.get("min_price")
        tiers = _tiers(r.get("price_str"))
        if price is None or len(tiers) < 2:
            continue
        if price not in tiers and (cuisine, r["name"]) not in UNRESOLVED_PRICE_DRIFT:
            offenders.append(f"{r['name']}: min_price {price} not among {tiers}")
    assert not offenders, "min_price matches no listed tier:\n  " + "\n  ".join(offenders)


def test_the_unresolved_drift_list_names_real_restaurants():
    # An entry for a restaurant that no longer exists would quietly excuse
    # nothing, exactly like a dead pin.
    for cuisine, name in UNRESOLVED_PRICE_DRIFT:
        names = {r["name"] for r in _rows(cuisine)}
        assert name in names, f"{cuisine}/{name} is exempted but not in restaurants.json"
