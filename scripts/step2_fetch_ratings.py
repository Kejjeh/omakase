"""
Step 2: Fetch Google Maps ratings via Places API for a given cuisine's restaurants.

Usage: python scripts/step2_fetch_ratings.py [--cuisine omakase] [--repair] [--force] [--dry-run]

--dry-run reports what a real run with the same flags would fetch and its
estimated cost, without reading the API key or touching the network. An
unknown argument is an error, raised before the key is read or anything is
sent: hand-rolled sys.argv checks ignore flags they do not know, and in a
sibling project that turned a mistyped dry run into a billed fetch.

Uses a per-cuisine cache to avoid re-fetching.

Text Search returns the restaurant's location and address alongside its rating,
so we persist those too — the neighborhood label is derived from the coordinates
downstream (see scripts/shared/geo.py) rather than trusted from the master sheet.

Entries cached before those fields were captured have a rating but no location.
The normal run skips anything already rated, so `--repair` exists to re-fetch
just those. A repair re-fetch also refreshes the rating, which can move
composite scores — run --dry-run first to see the blast radius.
"""

import argparse
import requests
import json
import time
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from shared import paths

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.shared.cities import city_for

# Set by configure() from the parsed arguments; nothing is read from sys.argv
# at import time.
CUISINE = None
RESTAURANTS_PATH = None
CACHE_PATH = None
SEARCH_TYPE = None
SEARCH_CITY = None
REPAIR = False
DRY_RUN = False
FORCE = False

# Places legacy Text Search, US list price per 1,000 calls. Only used to print
# the --dry-run estimate; every call (pinned Details lookups included) is
# costed at this rate.
TEXT_SEARCH_USD_PER_1000 = 32.0

# Restaurant names carry macrons (Sushi Ōmakase) that the Windows console's
# cp1252 default cannot encode — progress printing must never kill a paid run.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Fields a fully-populated cache entry carries. An entry missing any of these
# predates the geo work and needs a repair fetch.
GEO_FIELDS = ("lat", "lng", "address", "place_id")

# What kind of place this cuisine is about. Per-cuisine, not per-city: two
# cuisines in the same city can want different search terms. This was a
# `CUISINE == "philly"` ternary defaulting everything else to sushi, which
# meant Italian restaurants were searched as "<name> sushi New York City"
# (Lupa matched "Shin Takumi Omakase"). A cuisine must state its own type
# rather than inherit omakase's.
SEARCH_TYPE_BY_CUISINE = {
    "omakase": "sushi",
    "italian": "italian restaurant",
    "philly": "happy hour bar",
    "kensington": "restaurant",
}



def parse_args(argv=None):
    """Strict: an unknown or mistyped argument exits 2 here, before the key is
    read or a request is sent."""
    ap = argparse.ArgumentParser(
        prog="step2_fetch_ratings.py",
        description="Fetch Google Places ratings for one cuisine (billed).")
    ap.add_argument("--cuisine", "-c", choices=paths.CUISINES,
                    default=paths.DEFAULT_CUISINE)
    ap.add_argument("--repair", action="store_true",
                    help="re-fetch cached entries missing location fields")
    # Re-fetch every restaurant even if fully cached. Needed when the search
    # terms themselves change, since the cached entry is well-formed but
    # matched using the wrong query and no per-entry check can spot that.
    ap.add_argument("--force", action="store_true",
                    help="re-fetch every restaurant, cached or not")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be fetched and its cost; "
                         "no key, no network")
    return ap.parse_args(argv)


def configure(args):
    global CUISINE, RESTAURANTS_PATH, CACHE_PATH, SEARCH_TYPE, SEARCH_CITY
    global REPAIR, DRY_RUN, FORCE
    CUISINE = args.cuisine
    RESTAURANTS_PATH = paths.restaurants_json(CUISINE)
    CACHE_PATH = paths.ratings_cache(CUISINE)
    REPAIR, DRY_RUN, FORCE = args.repair, args.dry_run, args.force
    if CUISINE not in SEARCH_TYPE_BY_CUISINE:
        raise SystemExit(
            f"No search type for cuisine '{CUISINE}'. Add an entry to "
            f"SEARCH_TYPE_BY_CUISINE in {os.path.basename(__file__)} — a wrong "
            f"default silently matches the wrong restaurants."
        )
    SEARCH_TYPE = SEARCH_TYPE_BY_CUISINE[CUISINE]
    # The city comes from the shared table so it cannot disagree with the one
    # the Infatuation scraper and the geo lookup use.
    SEARCH_CITY = city_for(CUISINE).places_query


def api_key():
    """The Places key from the gitignored scripts/config.py. Read only on the
    billed path, after argument parsing, so --dry-run needs no config file."""
    from config import GOOGLE_API_KEY
    return GOOGLE_API_KEY


def load_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


EMPTY_RESULT = {
    "rating": None, "review_count": None, "google_name": "",
    "address": "", "lat": None, "lng": None, "place_id": None,
    "business_status": None,
}

# Fields to request from Place Details. Keep in step with EMPTY_RESULT.
DETAILS_FIELDS = (
    "name,formatted_address,geometry/location,place_id,"
    "rating,user_ratings_total,business_status"
)


def load_overrides():
    """Hand-pinned Google matches: {"Restaurant Name": "ChIJ..." | null}.

    A name search is not a stable identifier — Places substitutes a different
    business when a restaurant closes, is renamed, or shares a name with a
    sibling location. Once the right listing has been identified, pinning its
    id makes the lookup deterministic so it cannot drift back.

    A null pin means "this restaurant has no Google listing of its own; do not
    search". That is its own kind of correction: Masa has no listing and a name
    search lands on Bar Masa next door, so without a way to say 'stop looking'
    the pair would re-collide on every fetch.

    Values may be a bare id/null, or {"place_id": ..., "note": ...} carrying
    provenance for whoever reads the diff later.
    """
    path = paths.place_id_overrides(CUISINE)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return {
        name: (v if (v is None or isinstance(v, str)) else v.get("place_id"))
        # Underscore keys are documentation (JSON has no comments), not rows.
        for name, v in raw.items()
        if not name.startswith("_")
    }


def _shape(place):
    location = (place.get("geometry") or {}).get("location") or {}
    return {
        "rating": place.get("rating"),
        "review_count": place.get("user_ratings_total"),
        "google_name": place.get("name", ""),
        "address": place.get("formatted_address", ""),
        "lat": location.get("lat"),
        "lng": location.get("lng"),
        "place_id": place.get("place_id"),
        "business_status": place.get("business_status"),
    }


def fetch_by_place_id(place_id, api_key):
    """Look up a pinned listing by id. Deterministic — no fuzzy matching."""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {"place_id": place_id, "key": api_key, "fields": DETAILS_FIELDS}
    try:
        data = requests.get(url, params=params, timeout=10).json()
        if data.get("status") == "OK" and data.get("result"):
            return _shape(data["result"])
        print(f"  PINNED LOOKUP FAILED ({data.get('status')})", end=" ")
    except Exception as e:
        print(f"  ERROR: {e}")
    return dict(EMPTY_RESULT)


def search_place(name, neighborhood, api_key):
    """Search for a restaurant using the legacy Places Text Search API."""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    query = f"{name} {SEARCH_TYPE} {neighborhood} {SEARCH_CITY}"
    params = {"query": query, "key": api_key}

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("status") == "OK" and data.get("results"):
            return _shape(data["results"][0])
    except Exception as e:
        print(f"  ERROR: {e}")

    return dict(EMPTY_RESULT)


def needs_geo_repair(entry):
    """True if a cached entry has a rating but predates the location fields."""
    return entry.get("rating") is not None and any(
        entry.get(f) is None for f in GEO_FIELDS
    )


def action_for(entry, has_pin, pinned, force, repair):
    """-> "cached" | "repair" | "fetch" for one restaurant.

    The run loop and --dry-run both call this, so the dry run's count is the
    real run's count rather than a reimplementation of it.
    """
    # A pin means the cached match was wrong, so it must be applied even
    # when the cache looks complete — the stale entry is exactly the thing
    # being corrected. That includes a null pin, which has to clear a
    # wrongly-matched entry rather than leave it in place.
    pin_pending = has_pin and entry and entry.get("place_id") != pinned
    if entry and entry.get("rating") is not None and not force and not pin_pending:
        if not (repair and needs_geo_repair(entry)):
            return "cached"
        return "repair"
    return "fetch"


def billed_plan(restaurants, cache, overrides, force, repair):
    """-> (text_searches, details, detached): the calls a run would make.

    A null pin detaches without any call, so it is free.
    """
    text = details = detached = 0
    for r in restaurants:
        name = r["name"]
        has_pin = name in overrides
        pinned = overrides.get(name)
        if action_for(cache.get(name), has_pin, pinned, force, repair) == "cached":
            continue
        if has_pin and pinned is None:
            detached += 1
        elif pinned:
            details += 1
        else:
            text += 1
    return text, details, detached


def main(argv=None):
    configure(parse_args(argv))
    # Read before anything else on the billed path, as the old import-time
    # read was; never on the dry-run path.
    key = None if DRY_RUN else api_key()
    with open(RESTAURANTS_PATH, encoding="utf-8") as f:
        restaurants = json.load(f)

    cache = load_cache()
    overrides = load_overrides()

    new_fetches = 0
    repaired = 0
    cached = 0
    pinned_used = 0
    total = len(restaurants)
    if overrides:
        print(f"{len(overrides)} pinned place_id override(s) loaded\n")

    if DRY_RUN:
        missing = [r["name"] for r in restaurants if r["name"] not in cache
                   or cache[r["name"]].get("rating") is None]
        stale = [r["name"] for r in restaurants
                 if r["name"] in cache and needs_geo_repair(cache[r["name"]])]
        print(f"Cuisine: {CUISINE} ({total} restaurants)")
        print(f"  unfetched (always fetched):     {len(missing)}")
        print(f"  cached but missing location:    {len(stale)}  <- --repair re-fetches these")
        print(f"  complete:                       {total - len(missing) - len(stale)}")
        print("\nA repair also refreshes rating/review_count for those entries,")
        print("which can shift composite scores and rankings.")
        if stale:
            print(f"\nFirst 10 needing repair: {', '.join(stale[:10])}")
        text, details, detached = billed_plan(restaurants, cache, overrides,
                                              FORCE, REPAIR)
        calls = text + details
        flags = " ".join(f for f, on in (("--repair", REPAIR), ("--force", FORCE)) if on)
        print(f"\nWith these flags{f' ({flags})' if flags else ''}: {calls} billed "
              f"call(s) — {text} Text Search, {details} Details by pinned "
              f"place_id; {detached} null pin(s) detached at no cost.")
        print(f"Estimated cost: ${calls * TEXT_SEARCH_USD_PER_1000 / 1000:.2f} "
              f"at ${TEXT_SEARCH_USD_PER_1000:.0f}/1000 calls. "
              f"Dry run: no key read, nothing sent, nothing written.")
        return

    for i, r in enumerate(restaurants):
        name = r["name"]
        # The master sheet's label is unreliable, but it's only a search hint
        # here and Places tolerates a wrong one (distinctive restaurant names
        # dominate the match). Kept as-is to avoid changing existing matches.
        hood = r.get("neighborhood_raw") or r.get("neighborhood") or ""

        has_pin = name in overrides
        pinned = overrides.get(name)
        entry = cache.get(name)
        action = action_for(entry, has_pin, pinned, FORCE, REPAIR)
        if action != "fetch":
            if action == "cached":
                cached += 1
                print(f"[{i+1}/{total}] {name} -> CACHED ({entry['rating']})")
                continue
            print(f"[{i+1}/{total}] {name} -> REPAIR...", end=" ", flush=True)
            repaired += 1
        else:
            label = "PINNED" if has_pin else ("REFETCH" if (FORCE and entry) else "")
            print(f"[{i+1}/{total}] {name}...{label}", end=" ", flush=True)
            new_fetches += 1

        if has_pin and pinned is None:
            # Pinned to "no listing": clear whatever wrong business it matched
            # and stop. Leaving the old entry would recreate the collision.
            cache[name] = dict(EMPTY_RESULT)
            pinned_used += 1
            print("-> pinned to NO LISTING (detached)")
            continue

        if pinned:
            result = fetch_by_place_id(pinned, key)
            pinned_used += 1
        else:
            result = search_place(name, hood, key)
        # A failed lookup must not clobber a good cached rating — unless the
        # entry is pinned, where replacing the wrong match is the whole point.
        if result["rating"] is None and entry and entry.get("rating") is not None and not has_pin:
            print("-> LOOKUP FAILED, keeping cached entry")
            continue
        cache[name] = result
        print(f"-> {result['rating']} ({result['review_count']} reviews) [{result['google_name']}]")

        time.sleep(0.1)

        if (new_fetches + repaired) % 25 == 0:
            save_cache(cache)

    save_cache(cache)
    found = sum(1 for v in cache.values() if v.get("rating") is not None)
    located = sum(1 for v in cache.values() if v.get("lat") is not None)
    print(f"\nDone! {cached} cached, {new_fetches} new, {repaired} repaired.")
    if pinned_used:
        print(f"{pinned_used} looked up by pinned place_id (deterministic).")
    print(f"{found} entries with ratings, {located} with coordinates.")
    print(f"Saved to {CACHE_PATH}")

    _warn_on_collisions(cache, {r["name"] for r in restaurants})


def _warn_on_collisions(cache, on_sheet):
    """Two restaurants sharing a place_id proves one is matched to the wrong
    business. Surface it here so it is caught at fetch time rather than by an
    ad-hoc script weeks later."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scripts.shared.places import colliding_place_ids

    colliding = colliding_place_ids(cache, on_sheet)
    if not colliding:
        return
    print(f"\nWARNING: {len(colliding)} restaurants share a place_id with another.")
    print("At least one of each group is matched to the wrong business.")
    print("Pin the correct id in", paths.place_id_overrides(CUISINE))
    for name in sorted(colliding):
        print(f"  {name} -> {cache[name].get('google_name')}")


if __name__ == "__main__":
    main()
