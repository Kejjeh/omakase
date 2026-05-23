from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping


SOURCE_ORDER = ("google", "yelp", "infatuation")
SOURCE_CODES = {
    "google": "G",
    "yelp": "Y",
    "infatuation": "I",
}
DEFAULT_SOURCE_WEIGHTS = {
    "google": 0.35,
    "yelp": 0.45,
    "infatuation": 0.20,
}
AUTO_PRICE_EXPONENT_MIN_PAIRS = 5
AUTO_PRICE_EXPONENT_FALLBACK = 0.3
AUTO_PRICE_EXPONENT_MIN = 0.1
AUTO_PRICE_EXPONENT_MAX = 0.6


@dataclass(frozen=True)
class AdjustedReading:
    value: float
    n: int | None = None


@dataclass(frozen=True)
class ScoringConfig:
    weights: Mapping[str, float] = field(
        default_factory=lambda: dict(DEFAULT_SOURCE_WEIGHTS)
    )
    price_exponent: float | str = "auto"


@dataclass(frozen=True)
class Scoring:
    composite_rating: float
    sources: str
    value_score: float | None = None
    rating_percentile: float | None = None
    value_percentile: float | None = None


def score(restaurants, adjusted, config) -> dict[str, Scoring]:
    composites: dict[str, float] = {}
    sources_by_name: dict[str, str] = {}
    price_by_name: dict[str, float | None] = {}

    for restaurant in restaurants:
        name = restaurant["name"]
        weighted_parts = []
        source_codes = []

        for source in SOURCE_ORDER:
            reading = adjusted.get(source, {}).get(name)
            if reading is None:
                continue

            weighted_parts.append((reading.value, config.weights[source]))
            source_codes.append(SOURCE_CODES[source])

        if not weighted_parts:
            continue

        weight_total = sum(w for _, w in weighted_parts)
        composites[name] = sum(v * w for v, w in weighted_parts) / weight_total
        sources_by_name[name] = "+".join(source_codes)
        price_by_name[name] = restaurant.get("price")

    exponent = _resolve_exponent(composites, price_by_name, config)

    value_scores: dict[str, float | None] = {}
    for name, composite in composites.items():
        price = price_by_name[name]
        if price is None or price <= 0:
            value_scores[name] = None
        else:
            value_scores[name] = composite * (100 / price) ** exponent

    rating_pcts = _percentiles(composites)
    value_pcts = _percentiles(
        {n: v for n, v in value_scores.items() if v is not None}
    )

    return {
        name: Scoring(
            composite_rating=composites[name],
            sources=sources_by_name[name],
            value_score=value_scores[name],
            rating_percentile=rating_pcts.get(name),
            value_percentile=value_pcts.get(name),
        )
        for name in composites
    }


def _percentiles(values: dict[str, float]) -> dict[str, float]:
    n = len(values)
    if n == 0:
        return {}
    if n == 1:
        return {next(iter(values)): 1.0}

    # Average-rank ties: assign rank as mean of positions for equal values.
    sorted_items = sorted(values.items(), key=lambda kv: kv[1])
    ranks: dict[str, float] = {}
    i = 0
    while i < n:
        j = i
        while j + 1 < n and sorted_items[j + 1][1] == sorted_items[i][1]:
            j += 1
        avg_rank = (i + j) / 2 + 1  # positions are 1-indexed
        for k in range(i, j + 1):
            ranks[sorted_items[k][0]] = avg_rank
        i = j + 1

    return {name: (rank - 1) / (n - 1) for name, rank in ranks.items()}


def _resolve_exponent(composites, prices, config) -> float:
    if config.price_exponent != "auto":
        return float(config.price_exponent)

    pairs = [
        (composites[n], prices[n])
        for n in composites
        if prices.get(n) is not None and prices[n] > 0 and composites[n] > 0
    ]
    if len(pairs) < AUTO_PRICE_EXPONENT_MIN_PAIRS:
        return AUTO_PRICE_EXPONENT_FALLBACK

    n = len(pairs)
    log_r = [math.log(c) for c, _ in pairs]
    log_p = [math.log(p) for _, p in pairs]
    mean_p = sum(log_p) / n
    mean_r = sum(log_r) / n
    num = sum((lp - mean_p) * (lr - mean_r) for lp, lr in zip(log_p, log_r))
    den = sum((lp - mean_p) ** 2 for lp in log_p)
    if den == 0:
        return AUTO_PRICE_EXPONENT_FALLBACK
    beta = abs(num / den)
    return max(AUTO_PRICE_EXPONENT_MIN, min(AUTO_PRICE_EXPONENT_MAX, beta))
