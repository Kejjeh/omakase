"""
Step 2: Fetch Google Maps ratings via Places API for a given cuisine's restaurants.

Usage: python scripts/step2_fetch_ratings.py [--cuisine omakase] [--repair] [--dry-run]

Uses a per-cuisine cache to avoid re-fetching.

Text Search returns the restaurant's location and address alongside its rating,
so we persist those too — the neighborhood label is derived from the coordinates
downstream (see scripts/shared/geo.py) rather than trusted from the master sheet.

Entries cached before those fields were captured have a rating but no location.
The normal run skips anything already rated, so `--repair` exists to re-fetch
just those. A repair re-fetch also refreshes the rating, which can move
composite scores — run --dry-run first to see the blast radius.
"""

import requests
import json
import time
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from config import GOOGLE_API_KEY
from shared import paths

CUISINE = paths.parse_cuisine_arg()
RESTAURANTS_PATH = paths.restaurants_json(CUISINE)
CACHE_PATH = paths.ratings_cache(CUISINE)

REPAIR = "--repair" in sys.argv
DRY_RUN = "--dry-run" in sys.argv
# Re-fetch every restaurant even if fully cached. Needed when the search terms
# themselves change, since the cached entry is well-formed but matched using
# the wrong query and no per-entry check can spot that.
FORCE = "--force" in sys.argv

# Restaurant names carry macrons (Sushi Ōmakase) that the Windows console's
# cp1252 default cannot encode — progress printing must never kill a paid run.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Fields a fully-populated cache entry carries. An entry missing any of these
# predates the geo work and needs a repair fetch.
GEO_FIELDS = ("lat", "lng", "address", "place_id")

# Search configuration per cuisine. This was a `CUISINE == "philly"` ternary
# defaulting everything else to sushi-in-NYC, which silently mismatched every
# cuisine added afterwards: Italian restaurants were searched as "<name> sushi
# New York City" (Lupa matched "Shin Takumi Omakase"), and Kensington — which
# is in Philadelphia — was searched in New York. A cuisine must state its own
# terms rather than inherit omakase's by default.
SEARCH_CONFIG = {
    "omakase": {"city": "New York City", "type": "sushi"},
    "italian": {"city": "New York City", "type": "italian restaurant"},
    "philly": {"city": "Philadelphia", "type": "happy hour bar"},
    "kensington": {"city": "Philadelphia", "type": "restaurant"},
}

if CUISINE not in SEARCH_CONFIG:
    raise SystemExit(
        f"No search config for cuisine '{CUISINE}'. Add an entry to SEARCH_CONFIG "
        f"in {os.path.basename(__file__)} — a wrong default silently matches the "
        f"wrong restaurants."
    )
SEARCH_CITY = SEARCH_CONFIG[CUISINE]["city"]
SEARCH_TYPE = SEARCH_CONFIG[CUISINE]["type"]


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


def main():
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
        # A pin means the cached match was wrong, so it must be applied even
        # when the cache looks complete — the stale entry is exactly the thing
        # being corrected. That includes a null pin, which has to clear a
        # wrongly-matched entry rather than leave it in place.
        pin_pending = has_pin and entry and entry.get("place_id") != pinned
        if entry and entry.get("rating") is not None and not FORCE and not pin_pending:
            if not (REPAIR and needs_geo_repair(entry)):
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
            result = fetch_by_place_id(pinned, GOOGLE_API_KEY)
            pinned_used += 1
        else:
            result = search_place(name, hood, GOOGLE_API_KEY)
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
