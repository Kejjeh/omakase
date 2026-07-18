"""The override files are hand-edited, so they need guarding against rot.

A pin naming a restaurant that no longer exists is silently dead — it looks
like a correction is in force when nothing is being corrected.
"""
import json

import pytest

from scripts.shared import paths

CUISINES = paths.CUISINES


def _load(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _restaurant_names(cuisine):
    path = paths.restaurants_json(cuisine)
    if not path.exists():
        return set()
    return {r["name"] for r in json.loads(path.read_text(encoding="utf-8"))}


@pytest.mark.parametrize("cuisine", CUISINES)
def test_pinned_names_exist_on_the_master_sheet(cuisine):
    overrides = _load(paths.place_id_overrides(cuisine))
    names = _restaurant_names(cuisine)
    if not overrides or not names:
        pytest.skip(f"no overrides or no restaurants for {cuisine}")
    pinned = {k for k in overrides if not k.startswith("_")}
    assert pinned <= names, f"pinned but not on the master sheet: {sorted(pinned - names)}"


@pytest.mark.parametrize("cuisine", CUISINES)
def test_every_pin_carries_a_note_explaining_it(cuisine):
    # A bare id is unreviewable — the next reader cannot tell a researched pin
    # from a guess.
    overrides = _load(paths.place_id_overrides(cuisine))
    for name, value in overrides.items():
        if name.startswith("_"):
            continue
        assert isinstance(value, dict), f"{cuisine}/{name}: expected an object with a note"
        assert value.get("note"), f"{cuisine}/{name}: pin has no note"


@pytest.mark.parametrize("cuisine", CUISINES)
def test_pinned_place_ids_are_unique_within_a_cuisine(cuisine):
    # Pinning two restaurants to one id would hand-author the exact collision
    # the pins exist to remove.
    overrides = _load(paths.place_id_overrides(cuisine))
    ids = [
        v.get("place_id") for k, v in overrides.items()
        if not k.startswith("_") and isinstance(v, dict) and v.get("place_id")
    ]
    assert len(ids) == len(set(ids)), f"{cuisine}: duplicate pinned place_id"


@pytest.mark.parametrize("cuisine", CUISINES)
def test_asserted_closures_name_real_restaurants(cuisine):
    research = paths.research_dir(cuisine) / "closures_verified.json"
    if not research.exists():
        pytest.skip(f"no closures file for {cuisine}")
    records = json.loads(research.read_text(encoding="utf-8"))
    names = _restaurant_names(cuisine)
    for rec in records:
        assert rec["name"] in names, f"{cuisine}: closure asserted for unknown {rec['name']!r}"
        assert rec.get("caveat"), f"{cuisine}/{rec['name']}: closure has no stated evidence"


def test_masa_is_pinned_to_no_listing_and_never_marked_closed():
    """Regression: Masa is an operating 3-Michelin restaurant with no Places
    listing, so a name search lands on Bar Masa next door. It must stay
    detached and open — an automated pass once proposed closing it."""
    overrides = _load(paths.place_id_overrides("omakase"))
    assert "Masa" in overrides
    assert overrides["Masa"]["place_id"] is None

    closures = paths.research_dir("omakase") / "closures_verified.json"
    asserted = {r["name"] for r in json.loads(closures.read_text(encoding="utf-8"))}
    assert "Masa" not in asserted
