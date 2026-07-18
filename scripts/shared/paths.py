"""
Cuisine-aware path resolution. All pipeline scripts go through this so adding
a new cuisine = adding a folder, not editing path strings everywhere.

Layout:
  scripts/data/<cuisine>/master.xlsx           input
  scripts/data/<cuisine>/restaurants.json      after step 1
  scripts/data/<cuisine>/ratings_cache.json    Google: ratings + location
  scripts/data/<cuisine>/place_id_overrides.json  pinned Google matches
  scripts/data/<cuisine>/yelp_cache.json
  scripts/data/<cuisine>/infatuation_cache.json
  scripts/data/<cuisine>/scored_restaurants.json
  scripts/data/geo/                            neighborhood boundaries (shared)
  research_input/<cuisine>/                    optional specialty data
  docs/<cuisine>/index.html                    dashboard
"""
import os, pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

# Supported cuisines (extend as new ones are added)
CUISINES = ["omakase", "italian", "philly", "kensington"]
DEFAULT_CUISINE = "omakase"


def data_dir(cuisine):
    return PROJECT_ROOT / "scripts" / "data" / cuisine

def research_dir(cuisine):
    return PROJECT_ROOT / "research_input" / cuisine

def docs_dir(cuisine):
    return PROJECT_ROOT / "docs" / cuisine


def master_xlsx(cuisine):
    return data_dir(cuisine) / "master.xlsx"

def restaurants_json(cuisine):
    return data_dir(cuisine) / "restaurants.json"

def ratings_cache(cuisine):
    return data_dir(cuisine) / "ratings_cache.json"

def yelp_cache(cuisine):
    return data_dir(cuisine) / "yelp_cache.json"

def infatuation_cache(cuisine):
    return data_dir(cuisine) / "infatuation_cache.json"

def place_id_overrides(cuisine):
    return data_dir(cuisine) / "place_id_overrides.json"

def scored_json(cuisine):
    return data_dir(cuisine) / "scored_restaurants.json"

def dashboard_html(cuisine):
    return docs_dir(cuisine) / "index.html"


def parse_cuisine_arg(default=DEFAULT_CUISINE):
    """Lightweight arg parser. Looks for --cuisine X (or -c X) in sys.argv,
    returns default otherwise. Removes the flag from sys.argv in-place."""
    import sys
    argv = sys.argv
    for flag in ("--cuisine", "-c"):
        if flag in argv:
            idx = argv.index(flag)
            if idx + 1 < len(argv):
                cuisine = argv[idx + 1]
                del argv[idx:idx + 2]
                if cuisine not in CUISINES:
                    raise ValueError(f"Unknown cuisine '{cuisine}'. Known: {CUISINES}")
                return cuisine
    return default
