"""Pipeline: read -> score -> enrich -> write. One module, taking a Cuisine.

Refresh of source caches is out of scope here -- run the standalone fetchers
(`step1_read_master.py`, `step2_fetch_ratings.py`, `step2b_fetch_infatuation.py`,
plus the Yelp research prompts) when caches need updating. Pipeline reads the
caches as-is.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.scoring import ScoringConfig, score


def read(cuisine) -> list[dict]:
    return cuisine.read_restaurants()


def score_step(cuisine, restaurants: list[dict], config: ScoringConfig | None = None) -> dict:
    cfg = config or ScoringConfig()
    adjusted = {
        s.name: {r["name"]: s.read(r["name"]) for r in restaurants}
        for s in cuisine.sources
    }
    rows = [{"name": r["name"], "price": r.get("min_price")} for r in restaurants]
    return score(rows, adjusted, cfg)


def enrich(cuisine, restaurants: list[dict], scored: dict, user_state: dict) -> list[dict]:
    """Compose restaurant base records with per-source readings, composite scoring,
    free-form specialty data, and preserved user_state. Pure function -- no I/O."""
    specialties = cuisine.load_specialties()
    enriched: list[dict] = []
    for r in restaurants:
        name = r["name"]
        rec = dict(r)
        _merge_source_fields(rec, name, cuisine.sources)
        _merge_scoring(rec, scored.get(name))
        rec.update(specialties.get(name, {}))
        _merge_user_state(rec, user_state.get(name, {}))
        _finalize_legacy_shape(rec)
        enriched.append(rec)
    return enriched


_ROUND_3DP = (
    "composite_rating", "adjusted_rating", "value_score",
    "google_wilson", "yelp_wilson", "infatuation_5",
)
_PCT_FIELDS = ("rating_percentile", "value_percentile")


def _finalize_legacy_shape(rec: dict) -> None:
    for k in _ROUND_3DP:
        v = rec.get(k)
        if v is not None:
            rec[k] = round(v, 3)
    for k in _PCT_FIELDS:
        v = rec.get(k)
        if v is not None:
            rec[k] = round(v * 100, 1)
    # Specialty files use "confidence"; legacy dashboard reads "specialty_confidence".
    if "confidence" in rec:
        rec["specialty_confidence"] = rec.pop("confidence")
    rec.setdefault("closed", False)


def _merge_source_fields(rec: dict, name: str, sources: list) -> None:
    for s in sources:
        entry = s.entry(name)
        reading = s.read(name)
        if s.name == "google":
            rec["raw_rating"] = entry.get("rating") if entry else None
            rec["review_count"] = entry.get("review_count") if entry else None
            rec["google_name"] = entry.get("google_name", "") if entry else ""
            rec["google_wilson"] = reading.value if reading else None
        elif s.name == "yelp":
            rec["yelp_rating"] = entry.get("yelp_rating") if entry else None
            rec["yelp_count"] = entry.get("review_count") if entry else None
            rec["yelp_wilson"] = reading.value if reading else None
        elif s.name == "infatuation":
            rec["infatuation_rating"] = entry.get("rating") if entry else None
            rec["infatuation_5"] = reading.value if reading else None


def _merge_scoring(rec: dict, scoring) -> None:
    if scoring is None:
        return
    rec["composite_rating"] = scoring.composite_rating
    rec["adjusted_rating"] = scoring.composite_rating  # legacy alias
    rec["sources"] = scoring.sources
    rec["n_sources"] = scoring.sources.count("+") + 1
    rec["value_score"] = scoring.value_score
    rec["rating_percentile"] = scoring.rating_percentile
    rec["value_percentile"] = scoring.value_percentile


_USER_STATE_DEFAULTS = {
    "visited": False,
    "friend_suggested": False,
    "subway_walk_min": None,
    "nearest_456": None,
}


def _merge_user_state(rec: dict, state: dict) -> None:
    for key, default in _USER_STATE_DEFAULTS.items():
        rec[key] = state.get(key, default)


def write_scored_json(cuisine, enriched: list[dict], out_path: str | Path | None = None) -> Path:
    path = Path(out_path) if out_path else _default_data_dir(cuisine) / "scored_restaurants.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_dashboard_data(cuisine, enriched: list[dict], out_path: str | Path | None = None) -> Path:
    fields = cuisine.dashboard_fields()
    rows = [{k: r.get(k) for k in fields} for r in enriched]
    path = Path(out_path) if out_path else _default_dashboard_dir(cuisine) / "data.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return path


def _default_data_dir(cuisine) -> Path:
    return Path(__file__).resolve().parent / "data" / cuisine.name


def _default_dashboard_dir(cuisine) -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / cuisine.name


def load_user_state(cuisine) -> dict:
    path = _default_data_dir(cuisine) / "user_state.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


_EXCEL_HEADERS = [
    ("Restaurant Name", 30), ("Neighborhood", 30), ("Price ($)", 10),
    ("Pacing", 10), ("Vibe & Distinctions", 50),
    ("Commute (Parkchester)", 12), ("Commute (Park Slope)", 12), ("Time Diff", 10),
    ("Google Rating", 12), ("Review Count", 12),
    ("Adj. Rating", 11), ("Rating Pctl", 10),
    ("Value Score", 11), ("Value Pctl", 10),
    ("Visited", 8), ("Google Maps Name", 35),
]


def write_excel(cuisine, enriched: list[dict], out_path: str | Path | None = None) -> Path:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill

    root = Path(__file__).resolve().parents[1]
    path = Path(out_path) if out_path else root / f"{cuisine.name.capitalize()}_Ratings.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = cuisine.name.capitalize()
    hfont = Font(bold=True, size=11, color="FFFFFF")
    hfill = PatternFill("solid", fgColor="4472C4")
    visited_fill = PatternFill("solid", fgColor="E2EFDA")
    for col, (header, width) in enumerate(_EXCEL_HEADERS, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = hfont
        cell.fill = hfill
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = width
    for i, r in enumerate(enriched, 2):
        row_data = [
            r.get("name"), r.get("neighborhood"), r.get("min_price"),
            r.get("pacing"), r.get("vibe"),
            r.get("commute_parkchester", ""), r.get("commute_parkslope", ""), r.get("time_diff", ""),
            r.get("raw_rating"), r.get("review_count"),
            r.get("composite_rating"), r.get("rating_percentile"),
            r.get("value_score"), r.get("value_percentile"),
            "Yes" if r.get("visited") else "", r.get("google_name", ""),
        ]
        for col, val in enumerate(row_data, 1):
            cell = ws.cell(row=i, column=col, value=val)
            if r.get("visited"):
                cell.fill = visited_fill
    ws.freeze_panes = "A2"
    wb.save(path)
    return path
