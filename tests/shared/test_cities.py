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


# --- neighborhood slugs ---
#
# The Infatuation disambiguates same-named restaurants by neighborhood
# ("kalaya-fishtown"), but our labels are freeform, abbreviated, and sometimes
# name a borough plus two neighborhoods. Each candidate slug costs a request at
# a 2-second delay, so the list has to be both complete and tight.

def test_a_bare_neighborhood_slugs_directly():
    assert cities.neighborhood_slugs("Fishtown", cities.PHILADELPHIA) == ["fishtown"]


def test_a_borough_prefix_is_dropped():
    assert cities.neighborhood_slugs("Manhattan (Midtown East)", cities.NEW_YORK) == ["midtown-east"]


def test_an_em_dash_borough_prefix_is_dropped():
    assert cities.neighborhood_slugs("Manhattan — Upper East Side", cities.NEW_YORK) == ["upper-east-side"]


def test_local_abbreviations_expand_before_the_literal_form():
    # "NoLibs" is what we write; "northern-liberties" is what the URL uses.
    assert cities.neighborhood_slugs("NoLibs", cities.PHILADELPHIA) == ["northern-liberties", "nolibs"]
    assert cities.neighborhood_slugs("Manhattan (UES)", cities.NEW_YORK) == ["upper-east-side", "ues"]


def test_punctuated_abbreviations_still_match_their_alias():
    # "E. Kensington" and "E Kensington" are the same place written two ways.
    assert cities.neighborhood_slugs("E. Kensington", cities.PHILADELPHIA)[0] == "kensington"
    assert cities.neighborhood_slugs("Grad. Hospital", cities.PHILADELPHIA)[0] == "graduate-hospital"


def test_a_label_naming_several_neighborhoods_yields_all_of_them():
    slugs = cities.neighborhood_slugs("Manhattan (UES / Lower Manh.)", cities.NEW_YORK)
    assert "upper-east-side" in slugs
    assert "lower-manhattan" in slugs


def test_an_apostrophe_does_not_split_the_word():
    # Treating "'" as a separator produced "hell-s-kitchen", which matches
    # nothing on the site.
    assert cities.neighborhood_slugs("Manhattan (Hell's Kitchen)", cities.NEW_YORK) == ["hells-kitchen"]


def test_a_state_code_is_not_treated_as_a_neighborhood():
    # "Jersey City, NJ" — the "NJ" would otherwise cost a wasted request.
    assert cities.neighborhood_slugs("Jersey City, NJ", cities.NEW_YORK) == ["jersey-city"]


@pytest.mark.parametrize("label", [None, "", "   "])
def test_a_missing_label_yields_no_slugs(label):
    assert cities.neighborhood_slugs(label, cities.PHILADELPHIA) == []


def test_slugs_are_deduplicated():
    # "Olde Kensington" aliases to "kensington", which its generic form would
    # not repeat, but overlapping aliases must never produce duplicate requests.
    slugs = cities.neighborhood_slugs("Olde Kensington", cities.PHILADELPHIA)
    assert len(slugs) == len(set(slugs))
