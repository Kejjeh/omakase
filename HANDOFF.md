# Handoff — state of play (2026-09-01)

Read `CLAUDE.md` first (commands, gotchas, model routing). This file is what's done, what's broken, and what to do next.

## Done and working

- Full pipeline for all 4 cuisines: `python scripts/run.py --all` completes in seconds; regenerates scored JSON, dashboard `data.json`, and root Excel files. Verified 2026-09-01.
- Test suite: `python -m pytest tests/ -q` → **142 passed, 4 skipped, ~0.3s** (skips are data-conditional: philly/kensington have no override/closure files). Verified.
- Omakase (201 rows) and Italian (154 rows) dashboards: `docs/omakase/`, `docs/italian/`, linked from the `docs/index.html` landing page, served via GitHub Pages.
- Neighborhood derivation (NYC), trust-gated closure logic, place_id pinning (17 omakase pins, 2 italian), collision reporting — all covered by ADRs 0003–0006 and tests.

## In progress / half-finished

- **Philly + Kensington cuisines are data-only.** They score and write `docs/<cuisine>/data.json` but have **no `index.html` dashboard** and are not linked from the landing page. Their `yelp_cache.json` files are empty (`{}`), so they score on Google + Infatuation only. No Philadelphia neighborhood boundary set is registered (`cities.PHILADELPHIA.region = None`), so their hand-typed neighborhoods pass through unverified.
- **3 omakase place_id collision groups** (printed on every run, deliberately unresolved — ADR 0006 defers row removal to a human): Gyu-Ichiro + "Hiyake Omakase (Bowery)" (same place, renamed); Sushi Hayashi + "Sushi Hayashi (Williamsburg)" (duplicate row); "Omakase by No Name" + "Unique Omakase" (both resolve to "Omakase Sushi by No name"). Fixing means editing `scripts/data/omakase/master.xlsx` and re-running step1.

## Known bugs

1. **Two Italian rows carry another business's rating and rank high.** `Bar Tulia` (a Naples, FL concept with no NYC presence) matched "Tarallucci e Vino NoMad", composite 4.32; `Olmo` (only NYC Olmo is a Mexican cantina) matched "OLIO E PIÙ East Village", composite 4.39. No collision fires because Lodi was pinned away, leaving each id single-claimed. Repro: `python -c "import json; print([r for r in json.load(open('scripts/data/italian/ratings_cache.json',encoding='utf-8')).items() if r[0] in ('Bar Tulia','Olmo')])"`. Correct fix per ADR 0006 is removing the rows (owner decision — see Open questions); do NOT pin them to the wrong business.
2. **Untrusted Google matches still contribute their rating to the composite.** Trust gating (`shared/places.py`) protects derived fields (status, coordinates, neighborhood) but not the Reading itself — which is how bug 1 ranks. Methodology change → Opus territory.
3. `run.py --all --strict` exits non-zero — expected while the 3 collision groups above exist; not a regression.

## Prioritized next steps (each ≈ one Sonnet session unless marked Opus)

- **P0 — Resolve the bad Italian rows (blocked on Open question 1).** Once the owner rules, remove `Bar Tulia`/`Olmo` from `scripts/data/italian/restaurants.json` and their cache entries. Accept: rows gone from all italian JSON, `run.py --cuisine italian` clean, tests pass.
- **P0 — Resolve the 3 omakase duplicate rows (blocked on Open question 1).** Edit master.xlsx, re-run step1 + pipeline. Accept: `run.py --all --strict` exits 0; document in CLAUDE.md that --strict is now the standard check.
- **P1 — Philly/Kensington dashboards.** Copy `docs/italian/index.html`, trim to their `dashboard_fields()` (see `scripts/cuisines/philly.py` — much smaller field set), add landing-page cards. Accept: both pages render rows over `python -m http.server -d docs`.
- **P1 — Yelp coverage for philly/kensington.** Adapt `Yelp_Research_Prompt_italian.md` for each, run deep research, merge into their `yelp_cache.json` (match existing cache schema: `{name: {yelp_rating, review_count, ...}}`). Accept: scored output shows `Y` in `sources` for most rows.
- **P2 — Philadelphia neighborhood boundaries (Opus).** Register an OpenDataPhilly GeoJSON as a `geo.Region`, wire into `cities.PHILADELPHIA`. Accept: philly/kensington rows gain structured borough/nta fields; hand labels demoted to `neighborhood_raw` (mirror ADR 0003).
- **P2 — Trust-gate ratings, not just derived fields (Opus).** Decide whether an untrusted match's Reading should be excluded from the composite. Interacts with ADR 0005/0006; needs a before/after ranking diff.

## Open questions (owner input needed)

1. May agents remove rows (Bar Tulia, Olmo, the 3 omakase duplicate groups)? ADR 0006 reserves row removal for a human; nothing records whether that means "owner does it" or "owner approves an agent doing it".
2. Are `philly`/`kensington` still active goals, or parked? (Chose conservatively to document them as in-progress, not dead.)
3. Are `scripts/build_top12.js`, `build_top15.js`, and `final_docs/*.docx` still wanted? They're one-off docx generators with hardcoded data, stale relative to current scores. Left untouched.
4. The Google Places API key in the gitignored `scripts/config.py` — verified never committed to git history. Consider restricting/rotating it anyway since it predates this audit.

## Tech debt (known, not urgent)

- `name` as the universal join key; `place_id` is captured and nominated as successor (ADR 0004/0006).
- Two parallel path systems: `shared/paths.py` (step scripts) vs. adapter-internal paths (`cuisines/*.py`). Keep in sync when moving files.
- `scripts/add_new_candidates.py` and `scripts/import_italian_research.py` are completed one-off imports — safe to ignore, kept for provenance.
- Excel output bytes churn on every run (openpyxl timestamps) → perpetual dirty `*.xlsx` in `git status`.
- `pandas` is a dependency only for `step1_read_master.py`.
