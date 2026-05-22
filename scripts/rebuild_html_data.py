"""
Regenerates the ALL_DATA block in docs/<cuisine>/index.html from the cuisine's
scored_restaurants.json.

Usage: python scripts/rebuild_html_data.py [--cuisine omakase]
"""
import json, re, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from shared import paths

CUISINE = paths.parse_cuisine_arg()
scored = json.loads(paths.scored_json(CUISINE).read_text(encoding="utf-8"))

# Fields to embed in the HTML (keep only what the page uses)
KEEP = [
    "name", "neighborhood", "format", "price_str", "min_price", "pacing", "vibe",
    "parkchester_min", "parkslope_min", "time_diff",
    "raw_rating", "google_wilson", "review_count",
    "yelp_rating", "yelp_wilson", "yelp_count",
    "infatuation_rating", "infatuation_5",
    "composite_rating", "n_sources", "sources",
    "visited", "friend_suggested",
    "subway_walk_min", "nearest_456",
    "value_score", "rating_percentile", "value_percentile",
    # omakase-specific
    "wagyu_offered", "ayce_offered", "ayce_wagyu_offered",
    "wagyu_notes", "ayce_notes", "ayce_wagyu_notes",
    "premium_ingredients", "specialty_confidence", "closed", "caveat",
    # italian-specific
    "subtype", "famous_for", "tasting_format", "price_level", "typical_dinner_pp",
    "pasta_program", "pizza_program", "vintage", "reservation", "michelin",
    "address",
]

rows = []
for r in scored:
    row = {k: r.get(k) for k in KEEP}
    rows.append(row)

new_data_line = "const ALL_DATA = " + json.dumps(rows, ensure_ascii=False) + ";"

html_path = paths.dashboard_html(CUISINE)
html = html_path.read_text(encoding="utf-8")

# Replace the ALL_DATA assignment line (it's one long line)
html = re.sub(r"const ALL_DATA = \[.*?\];", new_data_line, html, count=1, flags=re.DOTALL)

html_path.write_text(html, encoding="utf-8")
print(f"[{CUISINE}] Updated ALL_DATA with {len(rows)} restaurants.")
