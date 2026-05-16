"""
Regenerates the ALL_DATA block in docs/index.html from scored_restaurants.json.
Run from the repo root: python scripts/rebuild_html_data.py
"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).parent.parent
scored = json.loads((ROOT / "scripts" / "scored_restaurants.json").read_text(encoding="utf-8"))
coords = json.loads((ROOT / "scripts" / "coords_cache.json").read_text(encoding="utf-8"))

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
    "wagyu_offered", "ayce_offered", "ayce_wagyu_offered",
    "wagyu_notes", "ayce_notes", "ayce_wagyu_notes",
    "premium_ingredients", "specialty_confidence", "closed", "caveat",
    "lat", "lng",
]

rows = []
for r in scored:
    row = {k: r.get(k) for k in KEEP}
    c = coords.get(r.get("name"))
    if c:
        row["lat"] = c.get("lat")
        row["lng"] = c.get("lng")
    rows.append(row)

new_data_line = "const ALL_DATA = " + json.dumps(rows, ensure_ascii=False) + ";"

html_path = ROOT / "docs" / "index.html"
html = html_path.read_text(encoding="utf-8")

# Replace the ALL_DATA assignment line (it's one long line)
html = re.sub(r"const ALL_DATA = \[.*?\];", new_data_line, html, count=1, flags=re.DOTALL)

html_path.write_text(html, encoding="utf-8")
with_coords = sum(1 for r in rows if r.get("lat") and r.get("lng"))
print(f"Updated ALL_DATA with {len(rows)} restaurants ({with_coords} with coords).")
