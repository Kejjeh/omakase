"""Guards on the cuisine -> city table.

The bug this table replaced appeared three separate times, each as a ternary
of the form `"philadelphia" if CUISINE == "philly" else "new-york"`. It reads
as "philly is the special case" but means "everything not named philly is in
New York", so every cuisine added afterwards silently inherited the wrong
city. These tests exist to make that class of mistake fail loudly.
"""
import pytest

from scripts.shared import cities, geo, paths


def test_every_registered_cuisine_has_a_city():
    # The whole point: a new cuisine must not fall through to a default.
    missing = [c for c in paths.CUISINES if c not in cities.CITY_BY_CUISINE]
    assert not missing, f"cuisines with no city registered: {missing}"


def test_an_unregistered_cuisine_raises_rather_than_guessing():
    with pytest.raises(KeyError) as exc:
        cities.city_for("a-cuisine-nobody-registered")
    assert "cities.py" in str(exc.value)


@pytest.mark.parametrize("cuisine", ["philly", "kensington"])
def test_philadelphia_cuisines_are_in_philadelphia(cuisine):
    # `kensington` is the one that broke: a Philadelphia dataset not named
    # "philly", so the old ternary sent it to New York. Its restaurants were
    # matched against Brooklyn sushi bars.
    city = cities.city_for(cuisine)
    assert city.places_query == "Philadelphia"
    assert city.infatuation_slug == "philadelphia"
    assert "nyc" not in city.slug_suffixes


@pytest.mark.parametrize("cuisine", ["omakase", "italian"])
def test_new_york_cuisines_are_in_new_york(cuisine):
    city = cities.city_for(cuisine)
    assert city.places_query == "New York City"
    assert city.infatuation_slug == "new-york"


def test_only_new_york_carries_neighborhood_boundaries():
    # Philadelphia has no OpenDataPhilly set registered, so it must derive
    # nothing rather than borrow NYC's polygons.
    assert cities.NEW_YORK.region is geo.NYC
    assert cities.PHILADELPHIA.region is None


def test_slug_suffixes_never_cross_cities():
    # Appending "-nyc" to a Philadelphia restaurant finds nothing; the old
    # scraper did exactly that for every restaurant regardless of city.
    assert "philly" not in cities.NEW_YORK.slug_suffixes
    assert "new-york" not in cities.PHILADELPHIA.slug_suffixes
