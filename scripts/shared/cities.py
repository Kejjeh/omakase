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

import re
import unicodedata
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
    #: How this city's shorthand neighborhood labels expand for a URL slug.
    #: The Infatuation disambiguates same-named restaurants by neighborhood
    #: ("kalaya-fishtown"), but our labels are abbreviated ("NoLibs") and the
    #: abbreviations are local to a city. Keys are compared casefolded with
    #: punctuation stripped; values are candidate slugs in preference order.
    neighborhood_aliases: dict[str, tuple[str, ...]]


NEW_YORK = City(
    key="nyc",
    places_query="New York City",
    infatuation_slug="new-york",
    slug_suffixes=("nyc", "new-york"),
    region=geo.NYC,
    neighborhood_aliases={
        "ues": ("upper-east-side",),
        "uws": ("upper-west-side",),
        "les": ("lower-east-side",),
        "fidi": ("financial-district",),
        "nomad": ("nomad",),
        "noho": ("noho",),
        "soho": ("soho",),
        "lower manh": ("lower-manhattan",),
        "midtown east": ("midtown-east",),
        "midtown west": ("midtown-west",),
        "east village": ("east-village",),
        "west village": ("west-village",),
        "hells kitchen": ("hells-kitchen",),
    },
)

PHILADELPHIA = City(
    key="philadelphia",
    places_query="Philadelphia",
    infatuation_slug="philadelphia",
    slug_suffixes=("philly", "philadelphia"),
    # No OpenDataPhilly boundary set registered yet, so Philadelphia cuisines
    # derive no neighborhood and keep their hand labels (ADR 0003).
    region=None,
    neighborhood_aliases={
        "nolibs": ("northern-liberties",),
        "e kensington": ("kensington", "east-kensington"),
        "olde kensington": ("kensington", "olde-kensington"),
        "grad hospital": ("graduate-hospital",),
        "washington sq": ("washington-square",),
        "south philly": ("south-philadelphia",),
    },
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


def _key(label: str) -> str:
    """Normalize a neighborhood label for alias lookup: 'E. Kensington' -> 'e kensington'.

    Apostrophes are dropped rather than treated as separators, so "Hell's
    Kitchen" keys as "hells kitchen" and slugs as "hells-kitchen" — splitting
    on the apostrophe produced "hell-s-kitchen", which matches nothing.
    """
    folded = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode()
    folded = folded.replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", " ", folded.lower()).strip()


def neighborhood_slugs(label: str | None, city: City) -> list[str]:
    """Candidate URL slugs for a neighborhood label, in preference order.

    Labels are freeform and messy — "Manhattan (UES / Lower Manh.)" names a
    borough and two neighborhoods, either of which might be the one The
    Infatuation used. So: drop the borough prefix, split the alternatives, and
    expand each through the city's aliases, falling back to a plain slugify.
    """
    if not label:
        return []
    # "Manhattan (Midtown East)" -> "Midtown East"; a bare label is left alone.
    inner = re.search(r"\(([^)]*)\)", label)
    body = inner.group(1) if inner else label
    body = re.sub(r"^(Manhattan|Brooklyn|Queens|Bronx|Staten Island)\b[\s—-]*", "", body).strip()

    out: list[str] = []
    for part in re.split(r"[/,]", body):
        key = _key(part)
        if not key:
            continue
        out.extend(city.neighborhood_aliases.get(key, ()))
        # Skip stubs like the "NJ" in "Jersey City, NJ" — a state code is never
        # a neighborhood slug, and each candidate costs a request.
        if len(key) >= 3:
            out.append(key.replace(" ", "-"))
    # Preserve order, drop repeats.
    return list(dict.fromkeys(out))


def region_for(cuisine_name: str) -> geo.Region | None:
    """Neighborhood boundaries for a cuisine, or None if we have none.

    Unlike city_for this tolerates an unknown cuisine, because deriving no
    neighborhood is a safe outcome — it leaves the hand label untouched.
    """
    city = CITY_BY_CUISINE.get(cuisine_name)
    return city.region if city else None
