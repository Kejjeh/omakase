"""
Step 2b: Fetch ratings from The Infatuation for our restaurant list.

Strategy:
  - Convert each restaurant name to a URL slug
  - Try multiple slug variants (with/without common suffixes like 'nyc', 'new-york')
  - Fetch the review page and extract the rating
  - Cache results to avoid re-fetching

The Infatuation uses a 1-10 scale with editorial reviews.
Not all restaurants will have reviews — we gracefully handle 404s.
"""

import json
import os
import re
import sys
import time
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import paths
from scripts.shared.cities import city_for

CUISINE = paths.parse_cuisine_arg()
RESTAURANTS_PATH = paths.restaurants_json(CUISINE)
CACHE_PATH = paths.infatuation_cache(CUISINE)

# Which city this cuisine covers — resolved from one table rather than a
# ternary, which previously meant "anything not named philly is New York" and
# would have scraped Philadelphia restaurants from the New York section.
CITY = city_for(CUISINE)
BASE_URL = f"https://www.theinfatuation.com/{CITY.infatuation_slug}/reviews/"

# Category words worth adding to or stripping from a slug when guessing a URL.
# Per-cuisine: trying "-omakase" on a Philadelphia Thai restaurant just burns a
# request. Empty is fine — the bare slug and the city-tagged variants still run.
CATEGORY_TERMS_BY_CUISINE = {
    "omakase": ("omakase", "sushi"),
    "italian": (),
    "philly": (),
    "kensington": (),
}
CATEGORY_TERMS = CATEGORY_TERMS_BY_CUISINE.get(CUISINE, ())
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
REQUEST_DELAY = 2  # seconds between requests — be respectful


def name_to_slugs(name):
    """
    Convert a restaurant name to possible Infatuation URL slugs.
    Returns a list of slug variants to try.
    """
    # Base slug: lowercase, strip special chars, spaces to hyphens
    slug = name.lower()
    # Remove possessives
    slug = slug.replace("'s", "s").replace("'s", "s")
    # Remove ampersands and special characters (not hyphens)
    slug = re.sub(r'[&+@#$%^*()!?,.:;\'"]+', '', slug)
    # Replace spaces and multiple hyphens with single hyphen
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')

    variants = [slug]

    # A restaurant may be listed with or without its category word — "Sushi
    # Noz" as "sushi-noz" or "noz". Which words are worth trying depends on the
    # cuisine: this ran the omakase rules for every cuisine, so it spent a
    # request asking The Infatuation for "kalaya-omakase", a Thai restaurant in
    # Philadelphia. At a 2-second delay per attempt that is not free.
    for term in CATEGORY_TERMS:
        if slug.endswith(f"-{term}"):
            variants.append(slug[: -len(term) - 1])
        elif slug.startswith(f"{term}-"):
            variants.append(slug[len(term) + 1:])
        elif term not in slug:
            variants.append(f"{slug}-{term}")

    # Restaurants are often listed with a city tag ("sushi-noz-nyc"). Which tag
    # depends on the city — appending "-nyc" to a Philadelphia restaurant, as
    # this did unconditionally, finds nothing.
    variants.extend(f"{slug}-{suffix}" for suffix in CITY.slug_suffixes)

    # Preserve order (first match wins) while dropping duplicates.
    return list(dict.fromkeys(variants))


def fetch_rating(slug):
    """
    Fetch The Infatuation rating for a given URL slug.
    Returns dict with rating info, or None if not found.
    """
    url = BASE_URL + slug
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if resp.status_code == 404:
            return None
        if resp.status_code != 200:
            print(f"    Unexpected status {resp.status_code} for {slug}")
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Extract rating
        rating_els = soup.select('div[data-testid="ratingBadge-rating"]')
        rating = None
        if rating_els:
            try:
                rating = float(rating_els[0].text.strip())
            except ValueError:
                pass

        # Extract restaurant name as confirmed by the site
        name_el = soup.select('h1')
        confirmed_name = name_el[0].text.strip() if name_el else None

        # Extract cuisine tags
        cuisine_els = soup.select('span.cuisineTag a[data-testid="tag-tagLink"]')
        cuisines = [el.text.strip() for el in cuisine_els]

        # Extract neighborhood
        location_els = soup.select('span.neighborhoodTag a[data-testid="tag-tagLink"]')
        neighborhood = location_els[0].text.strip() if location_els else None

        if rating is not None:
            return {
                "rating": rating,
                "infatuation_name": confirmed_name,
                "cuisine": cuisines,
                "neighborhood": neighborhood,
                "url": resp.url,
                "slug_used": slug,
            }

        return None

    except requests.RequestException as e:
        print(f"    Error fetching {slug}: {e}")
        return None


def main():
    # Load restaurant list
    with open(RESTAURANTS_PATH) as f:
        restaurants = json.load(f)

    # Load existing cache
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as f:
            cache = json.load(f)
        print(f"Loaded cache with {len(cache)} entries")
    else:
        cache = {}
        print("Starting fresh cache")

    found = 0
    not_found = 0
    skipped = 0
    total = len(restaurants)

    for i, r in enumerate(restaurants):
        name = r["name"]

        # Skip if already cached
        if name in cache:
            if cache[name].get("rating") is not None:
                found += 1
            else:
                not_found += 1
            skipped += 1
            continue

        print(f"[{i+1}/{total}] {name}")
        slugs = name_to_slugs(name)

        result = None
        for slug in slugs:
            print(f"    Trying: {slug}")
            result = fetch_rating(slug)
            if result is not None:
                print(f"    FOUND: {result['rating']}/10 ({result['infatuation_name']})")
                break
            time.sleep(0.5)  # Short delay between slug variants

        if result:
            cache[name] = result
            found += 1
        else:
            cache[name] = {"rating": None, "not_found": True}
            not_found += 1
            print(f"    Not reviewed on The Infatuation")

        # Save cache after each restaurant (in case of interruption)
        with open(CACHE_PATH, 'w') as f:
            json.dump(cache, f, indent=2)

        # Respectful delay between restaurants
        time.sleep(REQUEST_DELAY)

    print(f"\n{'='*60}")
    print(f"  THE INFATUATION SCRAPER RESULTS")
    print(f"{'='*60}")
    print(f"  Total restaurants: {total}")
    print(f"  Found with ratings: {found}")
    print(f"  Not reviewed: {not_found}")
    print(f"  Skipped (cached): {skipped}")
    print(f"  Cache saved to: {CACHE_PATH}")

    # Show what we found
    rated = {k: v for k, v in cache.items() if v.get("rating") is not None}
    if rated:
        print(f"\n  Rated restaurants ({len(rated)}):")
        for name, data in sorted(rated.items(), key=lambda x: x[1]["rating"], reverse=True):
            print(f"    {data['rating']:>4.1f}/10  {name}")


if __name__ == "__main__":
    main()
