"""
Step 3: Compute adjusted ratings and value scores (v2 — academic improvements).

Methodology:
  1. Google Bias Correction
     Google Maps ratings are systematically inflated vs other platforms.
     We apply a correction factor (default 0.97) to raw ratings before scoring.

  2. Wilson Score Lower Bound (replaces Bayesian average)
     Instead of pulling low-review restaurants toward a global mean, we compute
     the lower bound of a confidence interval around the true "approval rate."
     Adapts 5-star scale to a proportion: p = (rating - 1) / 4, then applies
     Wilson's formula with z = 1.96 (95% confidence).
     Effect: low-review places get wider uncertainty bands and lower scores.
     High-review places keep scores close to their observed rating.

  3. Empirical Price Exponent (replaces fixed 0.3)
     Instead of guessing how much price should matter, we derive it from the data.
     Log-log regression of rating vs price reveals the actual price elasticity
     for NYC omakase. This grounds the exponent in observed behavior.

  4. Percentile Ranking
     Since all ratings cluster between 4.2-5.0, raw differences are misleading.
     We add a percentile rank (0-100) showing where each restaurant falls
     relative to all others, making scores more interpretable.

  5. Value Score
     value = composite_rating * (100 / price) ^ price_exponent

  6. Specialty Merge
     If research_input/specialties_151.json and research_input/new_candidates_omakase.json
     exist, their wagyu/AYCE/premium-ingredient fields are merged onto each record.

  7. Preservation
     visited, friend_suggested, subway_walk_min, and nearest_456 are preserved
     from the previous scored_restaurants.json (if present), since those aren't
     derived from caches.

Outputs: scripts/scored_restaurants.json
"""

import json
import math
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    RATING_METHOD, WILSON_Z, BAYESIAN_M, GOOGLE_BIAS_CORRECTION,
    PRICE_EXPONENT, MAX_PRICE, VISITED,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESTAURANTS_PATH = os.path.join(PROJECT_ROOT, "scripts", "restaurants.json")
RATINGS_CACHE_PATH = os.path.join(PROJECT_ROOT, "scripts", "ratings_cache.json")
YELP_CACHE_PATH = os.path.join(PROJECT_ROOT, "scripts", "yelp_cache.json")
INFATUATION_CACHE_PATH = os.path.join(PROJECT_ROOT, "scripts", "infatuation_cache.json")
SPECIALTIES_151_PATH = os.path.join(PROJECT_ROOT, "research_input", "specialties_151.json")
NEW_CANDIDATES_PATH = os.path.join(PROJECT_ROOT, "research_input", "new_candidates_omakase.json")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "scripts", "scored_restaurants.json")


# ---------------------------------------------------------------------------
# Rating adjustment methods
# ---------------------------------------------------------------------------

def wilson_lower_bound(rating, review_count, max_val=5.0, z=WILSON_Z):
    """Wilson score lower bound adapted for a 1-max_val rating scale."""
    if rating is None or review_count is None or review_count == 0:
        return None
    p = (rating - 1.0) / (max_val - 1.0)
    n = review_count
    denominator = 1 + (z * z) / n
    center = p + (z * z) / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + (z * z) / (4 * n)) / n)
    lower = (center - spread) / denominator
    return round(lower * (max_val - 1.0) + 1.0, 3)


def bayesian_average(rating, review_count, global_mean, m):
    """Compute Bayesian average rating (legacy method)."""
    if rating is None or review_count is None or review_count == 0:
        return None
    v = review_count
    return (v / (v + m)) * rating + (m / (v + m)) * global_mean


def derive_price_exponent(ratings, prices):
    """
    Derive the price exponent empirically via log-log regression.

    log(quality) ~ beta * log(price) + intercept

    We use |beta| as the price exponent, capped between 0.1 and 0.6.
    """
    pairs = [(r, p) for r, p in zip(ratings, prices) if r is not None and p and p > 0]
    if len(pairs) < 5:
        return 0.3
    log_r = np.log(np.array([pair[0] for pair in pairs]))
    log_p = np.log(np.array([pair[1] for pair in pairs]))
    beta, _ = np.polyfit(log_p, log_r, 1)
    return max(0.1, min(0.6, abs(float(beta))))


def percentile(values, target):
    """Percentile rank of target within values (0-100). Ignores None."""
    if target is None:
        return None
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    rank = sum(1 for v in vals if v < target)
    return round(rank / len(vals) * 100, 1)


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    restaurants = load_json(RESTAURANTS_PATH, [])
    google_cache = load_json(RATINGS_CACHE_PATH, {})
    yelp_cache = load_json(YELP_CACHE_PATH, {})
    infatuation_cache = load_json(INFATUATION_CACHE_PATH, {})

    # Previous scored output: preserve subway_walk_min, nearest_456, friend_suggested, visited overrides
    prev_scored = load_json(OUTPUT_PATH, [])
    prev_by_name = {r["name"]: r for r in prev_scored}

    # Specialty data (optional)
    specialty_records = load_json(SPECIALTIES_151_PATH, []) + load_json(NEW_CANDIDATES_PATH, [])
    specialty_by_name = {r["name"]: r for r in specialty_records}

    # First pass: compute corrected ratings + Wilson scores
    rows = []
    for r in restaurants:
        name = r["name"]
        g = google_cache.get(name, {})
        y = yelp_cache.get(name, {})
        i = infatuation_cache.get(name, {})
        prev = prev_by_name.get(name, {})

        raw_g = g.get("rating")
        g_count = g.get("review_count") or 0
        g_corrected = raw_g * GOOGLE_BIAS_CORRECTION if raw_g else None

        if RATING_METHOD == "bayesian":
            g_adj = bayesian_average(g_corrected, g_count, 4.5, BAYESIAN_M) if g_corrected else None
        else:
            g_adj = wilson_lower_bound(g_corrected, g_count) if g_corrected else None

        y_rating = y.get("yelp_rating")
        y_count = y.get("review_count") or 0
        y_adj = wilson_lower_bound(y_rating, y_count) if y_rating else None

        inf_rating = i.get("rating")  # Infatuation uses 1-10
        inf_5 = round(((inf_rating - 1) / 9) * 4 + 1, 2) if inf_rating else None

        parts = [v for v in [g_adj, y_adj, inf_5] if v is not None]
        composite = round(sum(parts) / len(parts), 3) if parts else None

        source_codes = []
        if g_adj is not None: source_codes.append("G")
        if y_adj is not None: source_codes.append("Y")
        if inf_5 is not None: source_codes.append("I")
        sources = "+".join(source_codes)

        rows.append({
            "name": name,
            "neighborhood": r["neighborhood"],
            "price_str": r.get("price_str"),
            "min_price": r.get("min_price"),
            "pacing": r.get("pacing"),
            "vibe": r.get("vibe"),
            "commute_parkchester": r.get("commute_parkchester", ""),
            "commute_parkslope": r.get("commute_parkslope", ""),
            "time_diff": r.get("time_diff", ""),
            "raw_rating": raw_g,
            "google_wilson": g_adj,
            "review_count": g_count if g_count else None,
            "google_name": g.get("google_name", ""),
            "yelp_rating": y_rating,
            "yelp_wilson": y_adj,
            "yelp_count": y_count if y_count else None,
            "infatuation_rating": inf_rating,
            "infatuation_5": inf_5,
            "composite_rating": composite,
            "adjusted_rating": composite,  # alias for downstream consumers
            "n_sources": len(parts),
            "sources": sources,
            "visited": name in VISITED or prev.get("visited", False),
            "friend_suggested": prev.get("friend_suggested", False),
            "subway_walk_min": prev.get("subway_walk_min"),
            "nearest_456": prev.get("nearest_456"),
        })

    # Determine price exponent
    if isinstance(PRICE_EXPONENT, str) and PRICE_EXPONENT == "auto":
        ratings_for_fit = [r["composite_rating"] for r in rows]
        prices_for_fit = [r["min_price"] for r in rows]
        exp = derive_price_exponent(ratings_for_fit, prices_for_fit)
        print(f"Empirical price exponent: {exp:.3f}")
    else:
        exp = float(PRICE_EXPONENT)
        print(f"Fixed price exponent: {exp:.3f}")

    # Value scores
    for r in rows:
        if r["composite_rating"] is not None and r["min_price"] and r["min_price"] > 0:
            r["value_score"] = round(r["composite_rating"] * (100.0 / r["min_price"]) ** exp, 3)
        else:
            r["value_score"] = None

    # Percentiles (relative to the full dataset)
    all_ratings = [r["composite_rating"] for r in rows]
    all_values = [r["value_score"] for r in rows]
    for r in rows:
        r["rating_percentile"] = percentile(all_ratings, r["composite_rating"])
        r["value_percentile"] = percentile(all_values, r["value_score"])

    # Merge specialty fields
    for r in rows:
        sp = specialty_by_name.get(r["name"], {})
        r["wagyu_offered"] = sp.get("wagyu_offered")
        r["ayce_offered"] = sp.get("ayce_offered")
        r["ayce_wagyu_offered"] = sp.get("ayce_wagyu_offered")
        r["wagyu_notes"] = sp.get("wagyu_notes")
        r["ayce_notes"] = sp.get("ayce_notes")
        r["ayce_wagyu_notes"] = sp.get("ayce_wagyu_notes")
        r["premium_ingredients"] = sp.get("premium_ingredients") or []
        r["specialty_confidence"] = sp.get("confidence")
        r["closed"] = sp.get("closed", False)
        r["caveat"] = sp.get("caveat")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(rows)} restaurants to {OUTPUT_PATH}")
    print(f"  with composite rating: {sum(1 for r in rows if r['composite_rating'])}")
    print(f"  AYCE Wagyu: {sum(1 for r in rows if r.get('ayce_wagyu_offered'))}")
    print(f"  Wagyu offered: {sum(1 for r in rows if r.get('wagyu_offered'))}")
    print(f"  Marked closed: {sum(1 for r in rows if r.get('closed'))}")


if __name__ == "__main__":
    main()
