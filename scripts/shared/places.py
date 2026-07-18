"""How far to trust a Google Places match.

Places Text Search always returns *something*. When a restaurant has closed or
been renamed, it quietly returns a different, operating business with a similar
name — Robataya matched "Sushi By Bou - East Village", ROKI matched "RokuNana".
The cached record looks perfectly well-formed; it simply describes someone else.

That matters here because a wrong match's `business_status` describes the wrong
business. Deriving "is it open" from it would flip a genuinely-closed restaurant
back to open on the strength of its replacement's status. So anything derived
from a Places field has to be gated on whether the match can be trusted.

Two signals, in order of reliability:

1. Two restaurants sharing one `place_id` — at least one is wrong, and it is
   proof rather than inference.
2. Name similarity — weaker, and asymmetric in how it fails. "Mario's" vs
   "Mario's Restaurant of Arthur Avenue" is a correct match that scores badly,
   while "Omakase by Teisui" vs "Omakase By Tento" is a wrong match that scores
   well. Containment handles the first; nothing fully handles the second, which
   is why the threshold is set high and a near-miss is treated as untrusted.
"""
from __future__ import annotations

import difflib
import re
import unicodedata
from collections import defaultdict

# Tuned against the known-bad set: "Omakase by Teisui" vs "Omakase By Tento"
# scores 0.76 and must NOT pass, so the bar sits above it. Raising this only
# makes the pipeline more conservative — it derives less and defers to hand
# values more, which is the safe direction.
SIMILARITY_THRESHOLD = 0.80


def _normalize(s: str | None) -> str:
    """Casefold, strip accents and punctuation. 'Hōseki' -> 'hoseki'."""
    folded = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", folded.lower())


def name_similarity(ours: str | None, theirs: str | None) -> float:
    """0..1. Containment scores 1.0 — a longer official name is still a match."""
    a, b = _normalize(ours), _normalize(theirs)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def colliding_place_ids(cache: dict, names: set[str] | None = None) -> set[str]:
    """Restaurant names whose place_id is claimed by more than one restaurant.

    Pass `names` to score only restaurants currently on the master sheet;
    stale cache entries would otherwise manufacture false collisions.
    """
    by_id: dict[str, list[str]] = defaultdict(list)
    for name, entry in cache.items():
        if names is not None and name not in names:
            continue
        place_id = (entry or {}).get("place_id")
        if place_id:
            by_id[place_id].append(name)
    return {n for claimants in by_id.values() if len(claimants) > 1 for n in claimants}


def is_trustworthy(name: str, entry: dict | None, colliding: set[str] = frozenset()) -> bool:
    """Whether this Places match is solid enough to derive facts from."""
    if not entry or not entry.get("place_id"):
        return False
    if name in colliding:
        return False
    return name_similarity(name, entry.get("google_name")) >= SIMILARITY_THRESHOLD


def collision_groups(cache: dict, names: set[str] | None = None) -> list[list[str]]:
    """Restaurants grouped by the place_id they contend for, worst case first."""
    by_id: dict[str, list[str]] = defaultdict(list)
    for name, entry in cache.items():
        if names is not None and name not in names:
            continue
        place_id = (entry or {}).get("place_id")
        if place_id:
            by_id[place_id].append(name)
    groups = [sorted(v) for v in by_id.values() if len(v) > 1]
    return sorted(groups, key=lambda g: (-len(g), g[0]))


def describe_collisions(cache: dict, names: set[str] | None = None) -> str:
    """Human-readable collision report, empty string when there are none."""
    groups = collision_groups(cache, names)
    if not groups:
        return ""
    lines = [
        f"{sum(len(g) for g in groups)} restaurants in {len(groups)} group(s) "
        f"share a place_id; at least one per group is matched to the wrong business:"
    ]
    for group in groups:
        matched = (cache.get(group[0]) or {}).get("google_name")
        lines.append(f"  {' + '.join(group)}  -> all resolve to {matched!r}")
    return "\n".join(lines)
