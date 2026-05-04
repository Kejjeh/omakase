"""
Step 2: Fetch Google Maps ratings for all restaurants via Places API.
Uses a local cache (ratings_cache.json) to avoid re-fetching known restaurants.
Only fetches ratings for restaurants not already in the cache.

Outputs: scripts/ratings_cache.json
"""

import requests
import json
import time
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from config import GOOGLE_API_KEY, RATINGS_CACHE

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESTAURANTS_PATH = os.path.join(PROJECT_ROOT, "scripts", "restaurants.json")
CACHE_PATH = os.path.join(PROJECT_ROOT, RATINGS_CACHE)


def load_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def search_place(name, neighborhood, api_key):
    """Search for a restaurant using the legacy Places Text Search API."""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    query = f"{name} sushi {neighborhood} New York City"
    params = {"query": query, "key": api_key}

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("status") == "OK" and data.get("results"):
            place = data["results"][0]
            return {
                "rating": place.get("rating"),
                "review_count": place.get("user_ratings_total"),
                "google_name": place.get("name", ""),
                "address": place.get("formatted_address", ""),
            }
    except Exception as e:
        print(f"  ERROR: {e}")

    return {"rating": None, "review_count": None, "google_name": "", "address": ""}


def main():
    with open(RESTAURANTS_PATH) as f:
        restaurants = json.load(f)

    cache = load_cache()

    new_fetches = 0
    cached = 0
    total = len(restaurants)

    for i, r in enumerate(restaurants):
        name = r["name"]
        hood = r["neighborhood"]

        if name in cache and cache[name].get("rating") is not None:
            cached += 1
            print(f"[{i+1}/{total}] {name} -> CACHED ({cache[name]['rating']})")
            continue

        print(f"[{i+1}/{total}] {name}...", end=" ", flush=True)
        result = search_place(name, hood, GOOGLE_API_KEY)
        cache[name] = result
        new_fetches += 1
        print(f"-> {result['rating']} ({result['review_count']} reviews) [{result['google_name']}]")

        time.sleep(0.1)

        if new_fetches % 25 == 0:
            save_cache(cache)

    save_cache(cache)
    found = sum(1 for v in cache.values() if v.get("rating") is not None)
    print(f"\nDone! {cached} cached, {new_fetches} new fetches. {found} total with ratings.")
    print(f"Saved to {CACHE_PATH}")


if __name__ == "__main__":
    main()
