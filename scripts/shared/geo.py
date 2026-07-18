"""Derive a Restaurant's neighborhood from its coordinates.

The hand-entered `neighborhood` label on the master sheet is unreliable — it
disagreed with the actual coordinates in both directions (restaurants labelled
UES that sit in Midtown East, and a UES restaurant labelled UWS). Anything that
filters by neighborhood needs a label derived from geometry, not typing.

A Region bundles a boundary file with the property names it uses, so a second
city can be added by registering another Region rather than editing lookup
logic. NYC's NTA boundaries are vendored under `scripts/data/geo/`. Which
cuisine uses which Region is decided in `scripts/shared/cities.py`; the two
Philadelphia cuisines have no Region until an OpenDataPhilly boundary set is
added, and derive no neighborhood in the meantime.

Point-in-polygon is hand-rolled ray casting rather than shapely: the project
ships no dependency manifest, and a compiled geo stack is a steep price for
~30 lines over a few hundred points.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

GEO_DIR = Path(__file__).resolve().parent.parent / "data" / "geo"


@dataclass(frozen=True)
class Area:
    """A resolved neighborhood: the structured fields we store on a Restaurant."""

    code: str
    name: str
    borough: str


@dataclass(frozen=True)
class Region:
    """A city's neighborhood boundaries plus the property names they're keyed by."""

    key: str
    geojson: str
    code_prop: str
    name_prop: str
    borough_prop: str

    def path(self) -> Path:
        return GEO_DIR / self.geojson


NYC = Region(
    key="nyc",
    geojson="nyc_nta_2020.geojson",
    code_prop="nta2020",
    name_prop="ntaname",
    borough_prop="boroname",
)

# Which cuisine uses which Region lives in scripts/shared/cities.py, together
# with everything else that varies by city. This module owns boundaries and
# point-in-polygon only.


def _in_ring(x: float, y: float, ring: list) -> bool:
    """Ray casting against one linear ring."""
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        # Does the edge straddle the horizontal ray, and cross it to the right?
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _in_polygon(x: float, y: float, rings: list) -> bool:
    """rings[0] is the exterior; rings[1:] are holes punched out of it."""
    if not rings or not _in_ring(x, y, rings[0]):
        return False
    return not any(_in_ring(x, y, hole) for hole in rings[1:])


def _polygons(geometry: dict) -> list:
    kind, coords = geometry.get("type"), geometry.get("coordinates")
    if not coords:
        return []
    if kind == "Polygon":
        return [coords]
    if kind == "MultiPolygon":
        return coords
    return []


@lru_cache(maxsize=None)
def _features(region: Region) -> tuple:
    """Parsed boundary features, with a bounding box per polygon.

    Cached because the NYC file is ~2.4MB and every restaurant hits it. The
    bbox lets us reject most polygons on four comparisons instead of walking
    thousands of vertices.
    """
    data = json.loads(region.path().read_text(encoding="utf-8"))
    out = []
    for feature in data["features"]:
        props = feature.get("properties", {})
        area = Area(
            code=props.get(region.code_prop),
            name=props.get(region.name_prop),
            borough=props.get(region.borough_prop),
        )
        for rings in _polygons(feature.get("geometry") or {}):
            xs = [p[0] for p in rings[0]]
            ys = [p[1] for p in rings[0]]
            out.append((area, rings, (min(xs), min(ys), max(xs), max(ys))))
    return tuple(out)


def lookup(lat: float | None, lng: float | None, region: Region | None) -> Area | None:
    """Resolve coordinates to an Area, or None if outside the region / unknown."""
    if region is None or lat is None or lng is None:
        return None
    for area, rings, (min_x, min_y, max_x, max_y) in _features(region):
        if not (min_x <= lng <= max_x and min_y <= lat <= max_y):
            continue
        if _in_polygon(lng, lat, rings):
            return area
    return None




UNVERIFIED_SUFFIX = " (unverified)"


def display(borough: str | None, name: str | None,
            unverified_fallback: str | None = None) -> str:
    """Compose the human-readable label. Mirrors the dashboard's formatter.

    A restaurant can be underived for honest reasons — outside the region
    (Jersey City) or unfindable on Places — and its hand label may well be
    right. So the hand label is still shown, but never silently: it is marked
    unverified, because passing an unchecked label off as derived is the bug
    this module exists to fix. Callers opt in by name.
    """
    if borough and name:
        return f"{borough} ({name})"
    if unverified_fallback:
        return f"{unverified_fallback}{UNVERIFIED_SUFFIX}"
    return ""
