# Agent guide

## What this is

A data pipeline that ranks restaurants per cuisine (`omakase`, `italian` in NYC; `philly`, `kensington` in Philadelphia) by blending Google/Yelp/Infatuation ratings — Wilson-lower-bounded, weighted 0.35/0.45/0.20 — plus a price-adjusted value score, publishing a static dashboard per cuisine (`docs/`, GitHub Pages) and an Excel file per cuisine at the repo root. Python 3.13, no database, no web framework: every input and cache is committed JSON. **Current state: working.** Read `HANDOFF.md` for what's in progress and what to do next. Read `GLOSSARY.md` for the domain glossary — use its terms exactly.

## Commands (all verified from repo root)

```bash
pip install -r requirements.txt          # pandas, openpyxl, requests, beautifulsoup4, pytest
python -m pytest tests/ -q               # ~2.7s. Expect: 240 passed, 6 skipped
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
| `docs/adr/` | 7 ADRs — read the relevant one BEFORE touching anything it covers |

## Conventions and gotchas

- **Restaurants are keyed by `name`** — the join key across every cache. A shared `place_id` between two rows means a wrong Google match; `run.py` warns on every run. **There are no collisions today and `--strict` exits 0** — use it as the standard check. The 3 long-standing omakase groups were resolved 2026-11-07 on the owner's ruling (see HANDOFF.md). Two were genuine duplicate rows and were deleted; the third was **not** a duplicate — "Unique Omakase" is a distinct, now-closed restaurant whose name search fell through to its neighbour, and it is now a null pin. If a new collision appears, diagnose each group before assuming duplication: a shared `place_id` proves one of the rows is mismatched, not that the rows are the same restaurant.
- **Never hand-edit generated files**: `scored_restaurants.json`, `docs/*/data.json`, `*_Ratings.xlsx`.
- **The dashboard JavaScript has tests.** `tests/dashboard/` lifts functions out of the shipped `docs/<cuisine>/index.html` and runs them under the `node` on PATH (no JS runner, no new dependency; the tests skip if `node` is missing). `jsharness.py` does the extracting; the two test modules cover the headline stats and the filter/empty-state/chart-failure paths. Editing that HTML can therefore fail pytest — which is the point.
- **Inclusion source of truth differs by cuisine**: omakase = `scripts/data/omakase/master.xlsx` via step1; the other three = their `restaurants.json` directly (no master.xlsx exists for them).
- **Pins**: `place_id_overrides.json` makes a Google lookup deterministic. Every pin needs a `note` (test-enforced). A `null` pin means "no Google listing exists; do not search" (Masa). See ADR 0006.
- **An untrusted Google match contributes no rating.** Trust gating covers the Reading, not just the derived fields: a wrong-business match's rating is withheld from the composite and the remaining sources renormalize, with the reason carried onto the record (`excluded_sources`), the run log, the dashboards and the Excel file. 26 readings are excluded across the 4 cuisines today and 8 rows are left with no trusted source as a result — that is expected output, not a regression. See ADR 0007.
- **`closed_override` always beats Google's status**; fields from an untrusted Places match derive nothing. Deriving over an override reopened 7 genuinely closed restaurants once. See ADR 0005.
- **Neighborhood is derived from coordinates**, never from the hand label (`neighborhood_raw`, display-only with an "(unverified)" marker). See ADR 0003.
- Running the pipeline **always dirties the 4 root `.xlsx` files** even with no data change (openpyxl timestamp bytes). Expected; commit or ignore, don't investigate.
- Set `PYTHONUTF8=1` when running fetchers on Windows (restaurant names carry macrons).
- **Do not read these into context** (large, generated, or binary — see `.claudeignore`): `scripts/data/geo/nyc_nta_2020.geojson`, any `scored_restaurants.json` or `data.json`, `*.xlsx`, `final_docs/`, `research_input/italian/discovery.json`. Inspect them with `python -c` / jq instead.

## Skills for this repo

Load these with the Skill tool when the situation comes up; the user does not need to ask.

| Situation in this repo | Skill |
|---|---|
| A ranking, score or excluded count looks wrong | `diagnosing-bugs` |
| Writing or changing a fetcher, cache reader, match-trust check or `enrich` step | `sop-fail-loud` |
| A change alters `scored_restaurants.json`, `docs/*/data.json` or a `*_Ratings.xlsx` | `sop-regenerate-outputs` |
| A new place_id collision, "duplicate or distinct?", or whether a pin confers trust | `sop-owner-decision` |
| Changing weights, Wilson bounds, the price exponent or the trust threshold | `sop-owner-decision` (and escalate to Opus) |
| A data refresh that calls Google Places (billed) | ask the user first; then `/refresh-google` |
| Building a fix or feature test-first (scorer, sources, geo) | `tdd` |
| Changing a dashboard `index.html` | `/verify`, then serve `docs/` and check it in the browser (`verify`) |
| Before merging anything that moves numbers | `code-review` |

## Before you finish any task

1. `python -m pytest tests/ -q` → `240 passed, 6 skipped` (more passed is fine if you added tests).
2. `python scripts/run.py --all --strict` → exits 0 and prints **no** collision report. The `excluded:` / `no trusted source left for` lines are normal output (ADR 0007): expect `18 / 6 / 2 / 0` excluded and `7 / 0 / 1 / 0` with no trusted source, for omakase / italian / philly / kensington. Check the counts didn't move unless you meant them to.
3. `git diff --stat` → only files you meant to change, plus possible `.xlsx` churn.

## Model routing

Safe for Sonnet: doc updates; dashboard HTML/CSS tweaks; adding a pin (with a researched note); adding rows to `research_input/`; adding tests; running the refresh commands above; updating `user_state.json`; adding a new cuisine by copying an existing adapter + registering it in `cuisines/__init__.py` and `cities.py`.

Escalate to Opus: anything in `scripts/scoring/` (methodology — weights, Wilson, price exponent); the merge/derivation ordering in `pipeline.enrich` (`_merge_closed`, `_merge_geo`, `_merge_trust`); which sources `pipeline.TRUST_GATED_SOURCES` gates; the trust threshold or logic in `shared/places.py`; `shared/cities.py` semantics; any change that contradicts an ADR or spans multiple cuisines' data files.

## Issue tracker & domain docs

- Issues: GitHub Issues on `kejjeh/Omakase` via `gh` CLI — conventions in `docs/agents/issue-tracker.md`; labels in `docs/agents/triage-labels.md`.
- Domain language: `GLOSSARY.md` glossary + `docs/adr/` — usage rules in `docs/agents/domain.md`.
