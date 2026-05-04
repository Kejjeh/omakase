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
     value = wilson_rating * (100 / price) ^ price_exponent
     Now using bias-corrected Wilson lower bounds and an empirical exponent.

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
CACHE_PATH = os.path.join(PROJECT_ROOT, "scripts", "ratings_cache.json")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "scripts", "scored_restaurants.json")


# ---------------------------------------------------------------------------
# Rating adjustment methods
# ---------------------------------------------------------------------------

def wilson_lower_bound(rating, review_count, z=1.96):
    """
    Wilson score lower bound adapted for 5-star ratings.

    Converts the average star rating to a proportion (1-5 -> 0-1),
    computes the Wilson lower bound, then converts back to the star scale.

    This gives a conservative estimate of the "true" rating — places with
    few reviews get pulled down more than places with many reviews, but
    unlike Bayesian average, the pull is based on statistical uncertainty
    rather than an arbitrary confidence threshold.
    """
    if rating is None or review_count is None or review_count == 0:
        return None

    # Convert 5-star to proportion: 1.0 -> 0.0, 5.0 -> 1.0
    p = (rating - 1.0) / 4.0
    n = review_count

    # Wilson score lower bound
    denominator = 1 + (z * z) / n
    center = p + (z * z) / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + (z * z) / (4 * n)) / n)
    lower = (center - spread) / denominator

    # Convert back to 5-star scale
    return lower * 4.0 + 1.0


def bayesian_average(rating, review_count, global_mean, m):
    """Compute Bayesian average rating (legacy method)."""
    if rating is None or review_count is None or review_count == 0:
        return None
    v = review_count
    return (v / (v + m)) * rating + (m / (v + m)) * global_mean


def derive_price_exponent(ratings, prices):
    """
    Derive the price exponent empirically via log-log regression.

    In economics, the relationship between perceived value and price follows:
      log(quality) ~ beta * log(price) + intercept

    The coefficient beta tells us how much quality increases with price.
    We use |beta| as the price exponent, capped between 0.1 and 0.6.

    If beta is near 0, price barely predicts quality -> exponent should be low.
    If beta is high, pricier places are genuinely better -> exponent should be higher.
    """
   