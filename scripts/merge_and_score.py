"""
Recomputes scored_restaurants.json for the full dataset (now 188 restaurants).
- Uses restaurants.json as the canonical name+price+vibe source.
- Pulls Google ratings from ratings_cache.json (always), Yelp/Infatuation from caches when available.
- Computes Wilson lower bounds, composite rating, value score, percentiles.
- Merges specialty fields (wagyu/AYCE/...) from research_input/specialties_151.json + new_candidates_omakase.json.
- Preserves visited/friend_suggested + subway_walk_min/nearest_456 from previous scored_restaurants.json.
"""
import json, math, pathlib, sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from config import WILSON_Z, GOOGLE_BIAS_CORRECTION, VISITED

restaurants = json.loads((ROOT / "scripts" / "restaurants.json").read_text(encoding="utf-8"))
google = json.loads((ROOT / "scripts" / "ratings_cache.json").read_text(encoding="utf-8"))
yelp = json.loads((ROOT / "scripts" / "yelp_cache.json").read_text(encoding="utf-8"))
infat = json.loads((ROOT / "scripts" / "infatuation_cache.json").read_text(encoding="utf-8"))
prev_scored = json.loads((ROOT / "scripts" / "scored_restaurants.json").read_text(encoding="utf-8"))
prev_by_name = {r["name"]: r for r in prev_scored}

specialties_151 = json.loads((ROOT / "research_input" / "specialties_151.json").read_text(encoding="utf-8"))
new_omakase = json.loads((ROOT / "research_input" / "new_candidates_omakase.json").read_text(encoding="utf-8"))
specialty_by_name = {r["name"]: r for r in specialties_151 + new_omakase}


def wilson(rating, count, max_val=5.0, z=WILSON_Z):
    if rating is None or count is None or count == 0:
        return None
    p = (rating - 1.0) / (max_val - 1.0)
    n = count
    denom = 1 + (z * z) / n
    center = p + (z * z) / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + (z * z) / (4 * n)) / n)
    lo = (center - spread) / denom
    return round(lo * (max_val - 1.0) + 1.0, 3)


def percentile(values, target):
    if target is None:
        return None
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    rank = sum(1 for v in vals if v < target)
    return round(rank / len(vals) * 100, 1)


scored = []
for r in restaurants:
    name = r["name"]
    prev = prev_by_name.get(name, {})
    g = google.get(name, {})
    y = yelp.get(name, {})
    i = infat.get(name, {})

    raw_g = g.get("rating")
    g_count = g.get("review_count") or 0
    # Apply Google bias correction
    g_corrected = (raw_g * GOOGLE_BIAS_CORRECTION) if raw_g else None
    g_wilson = wilson(g_corrected, g_count) if g_corrected else None

    y_rating = y.get("yelp_rating")
    y_count = y.get("review_count") or 0
    y_wilson = wilson(y_rating, y_count) if y_rating else None

    inf_rating = i.get("rating")  # 1-10 scale
    inf_5 = round(((inf_rating - 1) / 9) * 4 + 1, 2) if inf_rating else None  # convert to 1-5

    # Composite: average of available wilson-style scores
    parts = [v for v in [g_wilson, y_wilson, inf_5] if v is not None]
    composite = round(sum(parts) / len(parts), 3) if parts else None
    n_sources = len(parts)
    source_codes = []
    if g_wilson is not None: source_codes.append("G")
    if y_wilson is not None: source_codes.append("Y")
    if inf_5 is not None: source_codes.append("I")
    sources = "+".join(source_codes) if source_codes else ""

    # Value score = composite * (100 / price)^0.3
    price = r.get("min_price")
    value_score = None
    if composite is not None and price and price > 0:
        value_score = round(composite * (100 / price) ** 0.3, 3)

    record = {
        "name": name,
        "neighborhood": r["neighborhood"],
        "price_str": r.get("price_str"),
        "min_price": price,
        "pacing": r.get("pacing"),
        "vibe": r.get("vibe"),
        "raw_rating": raw_g,
        "google_wilson": g_wilson,
        "review_count": g_count if g_count else None,
        "google_name": g.get("google_name", ""),
        "yelp_rating": y_rating,
        "yelp_wilson": y_wilson,
        "yelp_count": y_count if y_count else None,
        "infatuation_rating": inf_rating,
        "infatuation_5": inf_5,
        "composite_rating": composite,
        "n_sources": n_sources,
        "sources": sources,
        "visited": name in VISITED or prev.get("visited", False),
        "friend_suggested": prev.get("friend_suggested", False),
        "subway_walk_min": prev.get("subway_walk_min"),
        "nearest_456": prev.get("nearest_456"),
        "value_score": value_score,
        "rating_percentile": None,  # filled below
        "value_percentile": None,
    }

    # Merge specialty fields
    sp = specialty_by_name.get(name, {})
    record["wagyu_offered"] = sp.get("wagyu_offered")
    record["ayce_offered"] = sp.get("ayce_offered")
    record["ayce_wagyu_offered"] = sp.get("ayce_wagyu_offered")
    record["wagyu_notes"] = sp.get("wagyu_notes")
    record["ayce_notes"] = sp.get("ayce_notes")
    record["ayce_wagyu_notes"] = sp.get("ayce_wagyu_notes")
    record["premium_ingredients"] = sp.get("premium_ingredients") or []
    record["specialty_confidence"] = sp.get("confidence")
    record["closed"] = sp.get("closed", False)
    record["caveat"] = sp.get("caveat")

    scored.append(record)

# Compute percentiles
all_ratings = [r["composite_rating"] for r in scored]
all_values = [r["value_score"] for r in scored]
for r in scored:
    r["rating_percentile"] = percentile(all_ratings, r["composite_rating"])
    r["value_percentile"] = percentile(all_values, r["value_score"])

(ROOT / "scripts" / "scored_restaurants.json").write_text(
    json.dumps(scored, indent=2, ensure_ascii=False), encoding="utf-8"
)
print(f"Scored {len(scored)} restaurants.")
print(f"  with composite_rating: {sum(1 for r in scored if r['composite_rating'])}")
print(f"  AYCE Wagyu: {sum(1 for r in scored if r.get('ayce_wagyu_offered'))}")
print(f"  Wagyu offered: {sum(1 for r in scored if r.get('wagyu_offered'))}")
print(f"  Marked closed: {sum(1 for r in scored if r.get('closed'))}")
