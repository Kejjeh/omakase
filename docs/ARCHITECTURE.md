# Architecture

## Data flow, end to end

```
                     MANUAL / NETWORK REFRESH (run rarely, per cuisine)
 master.xlsx ──step1──> restaurants.json          (omakase only; others hand-maintained)
 Google Places ─step2─> ratings_cache.json        (rating, count, lat/lng, address,
                          ▲                        place_id, business_status)
 place_id_overrides.json ─┘ (pins force Details-by-id lookup instead of name search)
 Infatuation ──step2b─> infatuation_cache.json    (editorial 1-10)
 Deep-research prompt ─> yelp_cache.json          (no API; human pastes results)

                     PIPELINE (python scripts/run.py --all, offline, seconds)
 restaurants.json + caches
        │  scripts/cuisines/<cuisine>.py  (adapter: paths, sources, projection)
        ▼
 scoring.score()      Wilson-adjust readings, weighted blend G .35 / Y .45 / I .20
        │             (renormalized when a source is missing), value score, percentiles
        ▼
 pipeline.enrich()    merge: source fields -> scores -> specialties (research_input/)
        │             -> user_state.json -> derived neighborhood (geo) -> closed logic
        ▼
 writes: scripts/data/<cuisine>/scored_restaurants.json   (full record, debugging)
         docs/<cuisine>/data.json                         (dashboard_fields() projection)
         <Cuisine>_Ratings.xlsx                           (repo root, human-readable)

                     PRESENTATION
 docs/<cuisine>/index.html  fetches data.json at load (needs http://, not file://)
 docs/index.html            landing page linking omakase + italian dashboards
 GitHub Pages serves docs/ from main
```

## Key abstractions

- **Cuisine adapter** (`scripts/cuisines/*.py`, Protocol in `__init__.py`): owns where a cuisine's data lives, which sources it has, and which fields its dashboard gets. Adding a cuisine = new adapter + registry line + `cities.py` entry; the pipeline itself never changes.
- **RatingSource** (`scripts/sources/`): reads a committed JSON cache and returns an `AdjustedReading` (already Wilson-bounded / rescaled). `refresh()` deliberately raises — refreshing lives in the standalone step scripts, so the pipeline stays offline and deterministic.
- **Scorer** (`scripts/scoring/`): pure function over readings; no I/O. Price exponent is fit per cuisine by log-log regression, clamped to [0.1, 0.6], fallback 0.3.
- **enrich()** (`scripts/pipeline.py`): pure compose step. Trust and geo lookups are injected as callables so tests stub them. Merge order matters — derivation happens after specialties/user_state so overrides can win.
- **City registry** (`scripts/shared/cities.py`): everything that varies by city (search phrasing, Infatuation slugs, neighborhood boundaries) in one table; a missing entry raises rather than defaulting (a silent NYC default once mis-fetched all of Kensington).

## Why it's shaped this way

The repo grew from one omakase spreadsheet into four datasets. The recurring failure mode was *silent wrong joins*: name-based Google search substituting a different business, hand-typed neighborhoods disagreeing with coordinates, per-script city ternaries defaulting new cuisines to NYC. The structure exists to make every derivation explicit, gated on trust, and overridable by hand assertions (pins, `closed_override`). The 6 ADRs in `docs/adr/` each document one of these scars — read them before "simplifying" anything.

## Boundaries a change is likely to cross

- **Add/rename a dashboard field** → adapter `dashboard_fields()` + `pipeline.enrich`/merge helpers + `docs/<cuisine>/index.html` JS + possibly `_EXCEL_HEADERS`.
- **New cuisine** → `scripts/cuisines/<name>.py`, registry in `cuisines/__init__.py`, `cities.CITY_BY_CUISINE`, `step2_fetch_ratings.SEARCH_TYPE_BY_CUISINE`, data dir under `scripts/data/<name>/`, dashboard dir under `docs/<name>/`.
- **Scoring change** → `scripts/scoring/` + tests in `tests/scoring/` + rankings shift in every generated output (rerun `run.py --all`).
- **Anything touching Google data** → check `shared/places.py` trust rules and the pin files first.

## Non-obvious dependencies

- `step1` filters by `EXCLUDE_KEYWORDS`/`MAX_PRICE` from `scripts/config.py` — exclusion happens at read time, not scoring time.
- Point-in-polygon is hand-rolled (no shapely) against the vendored 2.4MB `scripts/data/geo/nyc_nta_2020.geojson`; Philadelphia has no boundary set yet, so `philly`/`kensington` keep hand-typed neighborhoods.
- `scripts/shared/paths.py` is a parallel path system used only by the step-fetcher scripts; the adapters build their own paths. Keep them consistent if you move data files.
