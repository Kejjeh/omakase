# Agent guide

## What this is

A data pipeline that ranks restaurants per cuisine (`omakase`, `italian` in NYC; `philly`, `kensington` in Philadelphia) by blending Google/Yelp/Infatuation ratings — Wilson-lower-bounded, weighted 0.35/0.45/0.20 — plus a price-adjusted value score, publishing a static dashboard per cuisine (`docs/`, GitHub Pages) and an Excel file per cuisine at the repo root. Python 3.13, no database, no web framework: every input and cache is committed JSON. **Current state: working.** Read `HANDOFF.md` for what's in progress and what to do next. Read `CONTEXT.md` for the domain glossary — use its terms exactly.

## Commands (all verified from repo root)

```bash
pip install -r requirements.txt          # pandas, openpyxl, requests, beautifulsoup4, pytest
python -m pytest tests/ -q               # ~0.3s. Expect: 142 passed, 4 skipped
python scripts/run.py --all              # rebuild all cuisines (score + write json/dashboard/excel)
python scripts/run.py --cuisine italian --steps score   # one cuisine, no file writes
python -m http.server -d docs 8000       # view dashboards; file:// does NOT work (ADR 0002)
```

Data refresh (network; each needs `scripts/config.py` — copy `config.example.py`, add a Google Places API key; the file is gitignored, NEVER commit it or paste the key anywhere):

```bash
python scripts/step1_read_master.py --cuisine omakase        # master.xlsx -> restaurants.json (omakase only)
python scripts/step2_fetch_ratings.py --cuisine omakase      # Google Places -> ratings_cache.json
python scripts/step2b_fetch_infatuation.py --cuisine omakase # Infatuation scrape -> infatuation_cache.json
```

Yelp has no fetcher: refresh is manual, via a deep-research session using `Yelp_Research_Prompt.md` (omakase) or `Yelp_Research_Prompt_italian.md`, merged into `scripts/data/<cuisine>/yelp_cache.json`.

## Architecture map (detail: docs/ARCHITECTURE.md)

| File | Role |
|---|---|
| `scripts/run.py` | CLI entry point; prints place_id collision report every run |
| `scripts/pipeline.py` | read → score → enrich → write (scored json, dashboard data.json, Excel) |
| `scripts/scoring/__init__.py` | pure scorer: weighted blend, value score, percentiles |
| `scripts/sources/__init__.py` | cache-reading sources; Wilson adjustment + Google 0.97 bias correction |
| `scripts/cuisines/*.py` | one adapter per cuisine: data paths, sources, `dashboard_fields()` projection |
| `scripts/shared/cities.py` | cuisine → city registry (search terms, slugs, boundaries); no defaults, raises |
| `scripts/shared/geo.py` | point-in-polygon neighborhood derivation from coordinates |
| `scripts/shared/places.py` | Google match trust: collisions + name similarity ≥ 0.80 |
| `scripts/shared/paths.py` | path helpers used by the step-fetcher scripts |
| `scripts/data/<cuisine>/` | committed inputs and caches (restaurants.json, *_cache.json, place_id_overrides.json, user_state.json) |
| `docs/<cuisine>/` | dashboard `index.html` + generated `data.json` |
| `docs/adr/` | 6 ADRs — read the relevant one BEFORE touching anything it covers |

## Conventions and gotchas

- **Restaurants are keyed by `name`** — the join key across every cache. A shared `place_id` between two rows means a wrong Google match; `run.py` warns on every run. **3 omakase collision groups (6 rows) are known duplicates awaiting a human decision — do not "fix" them** (see HANDOFF.md). Because of this, `--strict` currently fails on omakase; don't use it until those rows are resolved.
- **Never hand-edit generated files**: `scored_restaurants.json`, `docs/*/data.json`, `*_Ratings.xlsx`.
- **Inclusion source of truth differs by cuisine**: omakase = `scripts/data/omakase/master.xlsx` via step1; the other three = their `restaurants.json` directly (no master.xlsx exists for them).
- **Pins**: `place_id_overrides.json` makes a Google lookup deterministic. Every pin needs a `note` (test-enforced). A `null` pin means "no Google listing exists; do not search" (Masa). See ADR 0006.
- **`closed_override` always beats Google's status**; fields from an untrusted Places match derive nothing. Deriving over an override reopened 7 genuinely closed restaurants once. See ADR 0005.
- **Neighborhood is derived from coordinates**, never from the hand label (`neighborhood_raw`, display-only with an "(unverified)" marker). See ADR 0003.
- Running the pipeline **always dirties the 4 root `.xlsx` files** even with no data change (openpyxl timestamp bytes). Expected; commit or ignore, don't investigate.
- Set `PYTHONUTF8=1` when running fetchers on Windows (restaurant names carry macrons).
- **Do not read these into context** (large, generated, or binary — see `.claudeignore`): `scripts/data/geo/nyc_nta_2020.geojson`, any `scored_restaurants.json` or `data.json`, `*.xlsx`, `final_docs/`, `research_input/italian/discovery.json`. Inspect them with `python -c` / jq instead.

## Before you finish any task

1. `python -m pytest tests/ -q` → `142 passed, 4 skipped` (more passed is fine if you added tests).
2. `python scripts/run.py --all` → completes; the ONLY expected warning is the known 3-group omakase collision report.
3. `git diff --stat` → only files you meant to change, plus possible `.xlsx` churn.

## Model routing

Safe for Sonnet: doc updates; dashboard HTML/CSS tweaks; adding a pin (with a researched note); adding rows to `research_input/`; adding tests; running the refresh commands above; updating `user_state.json`; adding a new cuisine by copying an existing adapter + registering it in `cuisines/__init__.py` and `cities.py`.

Escalate to Opus: anything in `scripts/scoring/` (methodology — weights, Wilson, price exponent); the merge/derivation ordering in `pipeline.enrich` (`_merge_closed`, `_merge_geo`); the trust threshold or logic in `shared/places.py`; `shared/cities.py` semantics; any change that contradicts an ADR or spans multiple cuisines' data files.

## Issue tracker & domain docs

- Issues: GitHub Issues on `kejjeh/Omakase` via `gh` CLI — conventions in `docs/agents/issue-tracker.md`; labels in `docs/agents/triage-labels.md`.
- Domain language: `CONTEXT.md` glossary + `docs/adr/` — usage rules in `docs/agents/domain.md`.
