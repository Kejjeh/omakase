import pytest

from scripts.shared import geo
from scripts.shared.geo import Area, Region, _in_polygon, display, lookup, region_for


# --- point-in-polygon primitives (synthetic, no boundary file needed) ---

SQUARE = [[[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]]]
SQUARE_WITH_HOLE = SQUARE + [[[4, 4], [4, 6], [6, 6], [6, 4], [4, 4]]]


def test_point_inside_simple_polygon():
    assert _in_polygon(5, 5, SQUARE)


def test_point_outside_simple_polygon():
    assert not _in_polygon(15, 5, SQUARE)


def test_point_in_hole_is_outside_the_polygon():
    # A donut: inside the exterior but inside a hole means not in the area.
    assert not _in_polygon(5, 5, SQUARE_WITH_HOLE)


def test_point_in_donut_body_is_inside():
    assert _in_polygon(1, 1, SQUARE_WITH_HOLE)


def test_empty_rings_are_not_a_match():
    assert not _in_polygon(5, 5, [])


# --- regression cases: the mislabelled restaurants that motivated this ---
#
# Each is a real coordinate whose hand-entered label contradicted it. Addresses
# were verified against Google Places before being pinned here.

@pytest.mark.parametrize(
    ("name", "lat", "lng", "expected_nta", "wrong_hand_label"),
    [
        # 875 3rd Ave — labelled "Manhattan (UES)" on the master sheet.
        ("Atto Omakase", 40.75719, -73.96919, "East Midtown-Turtle Bay", "UES"),
        # Labelled "Manhattan (UES)".
        ("Tatsuda Omakase", 40.75920, -73.99130, "Hell's Kitchen", "UES"),
        # 411b Amsterdam Ave — Amsterdam is unambiguously UWS; labelled "UES / Lower Manh.".
        ("One Bite Omakase", 40.78349, -73.97778, "Upper West Side (Central)", "UES"),
        # 238 E 60th St — genuinely UES, but labelled "Manhattan (UWS)". Wrong the other way.
        ("Uka Omakase", 40.76142, -73.96473, "Upper East Side-Lenox Hill-Roosevelt Island", "UWS"),
    ],
)
def test_mislabelled_restaurants_resolve_to_their_real_neighborhood(
    name, lat, lng, expected_nta, wrong_hand_label
):
    area = lookup(lat, lng, geo.NYC)
    assert area is not None, f"{name} should resolve inside NYC"
    assert area.name == expected_nta
    assert area.borough == "Manhattan"


def test_lookup_returns_borough_and_code():
    area = lookup(40.76142, -73.96473, geo.NYC)
    assert area.borough == "Manhattan"
    assert area.code == "MN0801"


def test_point_outside_nyc_resolves_to_none():
    # Philadelphia City Hall — inside the bbox of nothing in the NYC set.
    assert lookup(39.9526, -75.1652, geo.NYC) is None


def test_coordinates_in_a_park_still_resolve():
    # Park NTAs are kept deliberately: a point in Central Park should get a
    # label, not None.
    area = lookup(40.7812, -73.9665, geo.NYC)
    assert area is not None
    assert area.name == "Central Park"


# --- missing data ---

@pytest.mark.parametrize(("lat", "lng"), [(None, -73.9), (40.7, None), (None, None)])
def test_missing_coordinates_resolve_to_none(lat, lng):
    assert lookup(lat, lng, geo.NYC) is None


def test_no_region_resolves_to_none():
    assert lookup(40.76142, -73.96473, None) is None


# --- region registry ---

def test_nyc_cuisines_map_to_the_nyc_region():
    assert region_for("omakase") is geo.NYC
    assert region_for("italian") is geo.NYC


def test_philadelphia_cuisines_have_no_region_yet():
    # philly/kensington are Philadelphia. They must resolve to None rather than
    # silently borrowing NYC boundaries.
    assert region_for("philly") is None
    assert region_for("kensington") is None


def test_unknown_cuisine_has_no_region():
    assert region_for("nonexistent") is None


# --- display ---

def test_display_composes_borough_and_name():
    assert display("Manhattan", "Upper East Side-Yorkville") == "Manhattan (Upper East Side-Yorkville)"


def test_display_is_empty_when_underived_and_no_fallback_offered():
    assert display(None, None) == ""


@pytest.mark.parametrize(("borough", "name"), [("Manhattan", None), (None, "Yorkville")])
def test_display_needs_both_halves_to_count_as_derived(borough, name):
    assert display(borough, name) == ""


def test_display_marks_a_fallback_label_as_unverified():
    # Jersey City is outside the NYC boundary set, so its hand label is all we
    # have — shown, but never passed off as derived.
    assert display(None, None, unverified_fallback="Jersey City, NJ") == "Jersey City, NJ (unverified)"


def test_derived_label_wins_over_an_offered_fallback():
    assert display("Manhattan", "Yorkville", unverified_fallback="Manhattan (UES)") == "Manhattan (Yorkville)"
