"""Which city each Cuisine covers, and everything that follows from that.

This exists because the same bug kept recurring. Three separate scripts each
re-derived a cuisine's city with its own ternary of the form:

    "philadelphia" if CUISINE == "philly" else "new-york"

which does not read as "philly is special" — it reads as "every cuisine that
is not literally named philly is in New York". Every cuisine added afterwards
inherited the wrong city silently. `kensington` is a Philadelphia dataset that
is not named `philly`, so its restaurants were searched on Google in New York
(Fiore matched a Brooklyn sushi bar) and would have been scraped from The
Infatuation's New York section too.

So the mapping lives once, here, and a cuisine with no entry raises rather
than defaulting to anything. Adding a city means adding a City; adding a
cuisine means adding a line to CITY_BY_CUISINE — neither means editing
lookup logic in three scripts.

What stays per-cuisine rather than per-city: the Google search *type*
("sushi", "happy hour bar"). That is a property of the dataset, not the city,
and lives in step2_fetch_ratings.SEARCH_CONFIG.
"""
from __future__ import annotations

from dataclasses import dataclass

from scripts.shared import geo


@dataclass(frozen=True)
class City:
    """Everything that varies by city across the source fetchers."""

    key: str
    #: How Google Places should be told where to look.
    places_query: str
    #: The Infatuation's URL segment: theinfatuation.com/<slug>/reviews/...
    infatuation_slug: str
    #: Suffixes worth trying on an Infatuation slug. Restaurants are often
    #: listed with a city tag ("sushi-noz-nyc"), and the right tag differs by
    #: city — appending "-nyc" to a Philadelphia restaurant finds nothing.
    slug_suffixes: tuple[str, ...]
    #: Neighborhood boundaries, or None where we have no boundary set.
    region: geo.Region | None


NEW_YORK = City(
    key="nyc",
    places_query="New York City",
    infatuation_slug="new-york",
    slug_suffixes=("nyc", "new-york"),
    region=geo.NYC,
)

PHILADELPHIA = City(
    key="philadelphia",
    places_query="Philadelphia",
    infatuation_slug="philadelphia",
    slug_suffixes=("philly", "philadelphia"),
    # No OpenDataPhilly boundary set registered yet, so Philadelphia cuisines
    # derive no neighborhood and keep their hand labels (ADR 0003).
    region=None,
)


CITY_BY_CUISINE = {
    "omakase": NEW_YORK,
    "italian": NEW_YORK,
    "philly": PHILADELPHIA,
    "kensington": PHILADELPHIA,
}


def city_for(cuisine_name: str) -> City:
    """The city a cuisine covers. Raises rather than guessing."""
    try:
        return CITY_BY_CUISINE[cuisine_name]
    except KeyError:
        raise KeyError(
            f"No city registered for cuisine {cuisine_name!r}. Add one to "
            f"CITY_BY_CUISINE in scripts/shared/cities.py — a default would "
            f"silently search the wrong city."
        ) from None


def region_for(cuisine_name: str) -> geo.Region | None:
    """Neighborhood boundaries for a cuisine, or None if we have none.

    Unlike city_for this tolerates an unknown cuisine, because deriving no
    neighborhood is a safe outcome — it leaves the hand label untouched.
    """
    city = CITY_BY_CUISINE.get(cuisine_name)
    return city.region if city else None
