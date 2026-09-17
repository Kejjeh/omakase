# Handoff — state of play (2026-09-17)

Read `CLAUDE.md` first (commands, gotchas, model routing). This file is what's done, what's broken, and what to do next.

## Done and working

- Full pipeline for all 4 cuisines: `python scripts/run.py --all` completes in seconds; regenerates scored JSON, dashboard `data.json`, and root Excel files. Verified 2026-09-01.
- Test suite: `python -m pytest tests/ -q` → **196 passed, 4 skipped, ~0.6s** (skips are data-conditional: philly/kensington have no override/closure files). Verified 2026-09-17.
- Omakase (201 rows) and Italian (154 rows) dashboards: `docs/omakase/`, `docs/italian/`, linked from the `docs/index.html` landing page, served via GitHub Pages.
- Neighborhood derivation (NYC), trust-gated closure logic, place_id pinning (17 omakase pins, 2 italian), collision reporting — all covered by ADRs 0003–0006 and tests.
- **Trust-gated Readings (ADR 0007, 2026-09-17).** An untrusted Google match no longer contributes its rating to the Composite rating. Was known bug 2 below; now fixed, tested and documented. Test suite is **196 passed, 4 skipped**.

## In progress / half-finished

- **Philly + Kensington cuisines are data-only.** They score and write `docs/<cuisine>/data.json` but have **no `index.html` dashboard** and are not linked from the landing page. Their `yelp_cache.json` files are empty (`{}`), so they score on Google + Infatuation only. No Philadelphia neighborhood boundary set is registered (`cities.PHILADELPHIA.region = None`), so their hand-typed neighborhoods pass through unverified.
- **3 omakase place_id collision groups** (printed on every run, deliberately unresolved — ADR 0006 defers row removal to a human): Gyu-Ichiro + "Hiyake Omakase (Bowery)" (same place, renamed); Sushi Hayashi + "Sushi Hayashi (Williamsburg)" (duplicate row); "Omakase by No Name" + "Unique Omakase" (both resolve to "Omakase Sushi by No name"). Fixing means editing `scripts/data/omakase/master.xlsx` and re-running step1.

## Known bugs

1. **Two Italian rows still exist for businesses we don't want.** `Bar Tulia` (a Naples, FL concept with no NYC presence) and `Olmo` (the only NYC Olmo is a Mexican cantina) are still rows in `scripts/data/italian/restaurants.json`. They no longer *rank* on the wrong business's rating — ADR 0007 withheld those Readings, dropping Bar Tulia out of the ranking entirely and Olmo from #6 to #85 on Infatuation alone — but the rows themselves are still there. Correct fix per ADR 0006 is removing them (owner decision — see Open questions); do NOT pin them to the wrong business.
2. ~~Untrusted Google matches still contribute their rating to the composite.~~ **Fixed 2026-09-17, ADR 0007.**
3. `run.py --all --strict` exits non-zero — expected while the 3 collision groups above exist; not a regression. It was NOT weakened to accommodate ADR 0007.

## Prioritized next steps (each ≈ one Sonnet session unless marked Opus)

- **P0 — Resolve the bad Italian rows (blocked on Open question 1).** Once the owner rules, remove `Bar Tulia`/`Olmo` from `scripts/data/italian/restaurants.json` and their cache entries. Accept: rows gone from all italian JSON, `run.py --cuisine italian` clean, tests pass.
- **P0 — Resolve the 3 omakase duplicate rows (blocked on Open question 1).** Edit master.xlsx, re-run step1 + pipeline. Accept: `run.py --all --strict` exits 0; document in CLAUDE.md that --strict is now the standard check.
- **P1 — Philly/Kensington dashboards.** Copy `docs/italian/index.html`, trim to their `dashboard_fields()` (see `scripts/cuisines/philly.py` — much smaller field set), add landing-page cards. Accept: both pages render rows over `python -m http.server -d docs`.
- **P1 — Yelp coverage for philly/kensington.** Adapt `Yelp_Research_Prompt_italian.md` for each, run deep research, merge into their `yelp_cache.json` (match existing cache schema: `{name: {yelp_rating, review_count, ...}}`). Accept: scored output shows `Y` in `sources` for most rows.
- **P2 — Philadelphia neighborhood boundaries (Opus).** Register an OpenDataPhilly GeoJSON as a `geo.Region`, wire into `cities.PHILADELPHIA`. Accept: philly/kensington rows gain structured borough/nta fields; hand labels demoted to `neighborhood_raw` (mirror ADR 0003).
- ~~**P2 — Trust-gate ratings, not just derived fields (Opus).**~~ **Done 2026-09-17 — ADR 0007.** Measured ranking diff is recorded below.
- **P1 — Rule on the 7 look-correct exclusions (owner, then ≈ one Sonnet session).** See "What ADR 0007 excluded" below. Several are certainly correct matches losing a good Reading; the remedy needs an owner ruling first (Open question 5).

## What ADR 0007 excluded (measured, `run.py --all` on the committed caches)

34 Google Readings withheld across the 4 cuisines; 13 rows left with no trusted source and therefore **no Composite rating at all** (not zero — absent, and absent from the percentile cohorts). No rows were removed, no cache was edited, no `closed` value changed (omakase 26, italian 8, philly 0, kensington 0 before and after).

| Cuisine | Excluded | Reason breakdown | Rows now unrated | Headline rank moves |
|---|---|---|---|---|
| omakase | 24 | 18 name_mismatch, 6 place_id_collision | 11 | Niku X NYC #7 → unrated; Sushi Daizen #19 → unrated; Kun Tsuki #80 → #134; Sake Kawa #99 → #47 |
| italian | 8 | 8 name_mismatch | 1 | Bar Tulia #15 → unrated; Olmo #6 → #85; Trattoria L'Incontro #40 → #128 |
| philly | 2 | 2 name_mismatch | 1 | Bob & Barbara's #3 → unrated |
| kensington | 0 | — | 0 | none (only the two new annotation fields appear) |

Fields that changed anywhere in `scored_restaurants.json`: `composite_rating`, `adjusted_rating`, `value_score`, `rating_percentile`, `value_percentile`, `sources`, `n_sources`, `google_wilson` (nulled when excluded), plus the new `google_trusted` and `excluded_sources`. Nothing else — `closed`, `closed_override`, `business_status`, coordinates, `neighborhood_raw`, `raw_rating`, `review_count` and `place_id` are all byte-identical.

**Not every exclusion is a wrong match.** These look correct to a human and lost a good Reading to the 0.80 name-similarity bar. They need an owner ruling, not an agent's guess — see Open question 5:

| Row | Google returned | Similarity | Cost |
|---|---|---|---|
| Sottocasa Harlem (italian) | Sottocasa Pizzeria Harlem | 0.79 | #57 → #129 |
| Zero Otto Nove (Trattoria) (italian) | Zero Otto Nove Bronx | 0.74 | #72 → #130 |
| Trattoria L'Incontro (italian) | L'incontro by Rocco | 0.53 | #40 → #128 |
| Il Mulino New York (italian) | Il Mulino - Downtown (West 3rd) | 0.58 | #90 → #138 |
| Bob & Barbara's (philly) | Bob and Barbara's Lounge | 0.71 | #3 → unrated |
| Bar Lesieur (philly) | The Lesieur | 0.70 | #23 → #23 |
| Niku X NYC (omakase) | NIKU X \| Limitless Wagyu BBQ & Seafood | 0.32 | #7 → unrated |

(Genuinely wrong matches in the same set, for contrast: Olmo → OLIO E PIÙ (0.26), Bar Tulia → Tarallucci e Vino (0.36), ROKI → RokuNana (0.50), Omakase by Teisui → Omakase By Tento (0.76).)

## Review corrections on top of ADR 0007 (2026-09-17)

Two defects found in independent review of the trust-gating branch, both in the dashboards only — no scoring, threshold, pin, row or weight changed, and `run.py --all` reproduced the committed JSON byte-for-byte (only the usual `.xlsx` timestamp churn).

- **"Best Value" could name an unrated restaurant.** `updateStats()` reduced over every filtered row with `(r.value_score||0)`, so a row whose Reading was withheld — value score `null`, treated as `0` — won by default whenever the filter left nothing corroborated. With the "Incl. unrated" filter on omakase it printed a restaurant name next to an average rating of `-`. The reduce now runs over rows that have both a Composite rating and a value score, keeps the existing corroborated-source preference among those, and shows `-` when the filter leaves none. A row with no price has no value score either, so it is not a candidate.
- **The badge legend overclaimed.** It read "Google match is a different business". A name mismatch, a place_id collision or a missing id is evidence the match *cannot be verified*, not proof it is wrong — the table above lists seven exclusions that look correct. It now reads "Google match could not be verified — rating withheld". The per-row hover text was already factual (it names the listing Places returned and the similarity score) and was left alone.

New tests: `tests/dashboard/test_dashboard_stats.py` lifts `updateStats()` out of the shipped `index.html` and runs it under `node` (no JS runner, no new dependency; skips if `node` is absent), covering all-unrated, mixed rated/unrated, null-price, corroborated-vs-bargain, the single-source fallback, empty filter, and average-rating-ignores-unrated — parametrized over both dashboards. Verified failing against the pre-fix file. Browser check with only-unrated rows: `avg -`, `best -`, no console errors on either dashboard.

## Open questions (owner input needed)

1. May agents remove rows (Bar Tulia, Olmo, the 3 omakase duplicate groups)? ADR 0006 reserves row removal for a human; nothing records whether that means "owner does it" or "owner approves an agent doing it".
2. Are `philly`/`kensington` still active goals, or parked? (Chose conservatively to document them as in-progress, not dead.)
3. Are `scripts/build_top12.js`, `build_top15.js`, and `final_docs/*.docx` still wanted? They're one-off docx generators with hardcoded data, stale relative to current scores. Left untouched.
4. The Google Places API key in the gitignored `scripts/config.py` — verified never committed to git history. Consider restricting/rotating it anyway since it predates this audit.
5. **Should a pin confer trust?** ADR 0006 makes a pinned `place_id` deterministic and CONTEXT.md calls a pin an Override — a hand assertion that beats a derived value. Name similarity *is* a derived value, but it currently overrules the pin, so pinning `Sottocasa Harlem` to the correct listing would **not** bring its Reading back. Every pin in the repo today scores ≥ 0.86 or is a null pin, so the change would alter no current output; it was deliberately left out of ADR 0007 rather than smuggled in. Ruling yes gives the table above a one-pin-each remedy. Ruling no means those rows stay unrated until the rows or the threshold change — and the threshold must not move (ADR 0007, cautions).

## Housekeeping

- The GitHub repo was renamed to `Kejjeh/omakase`; old remote URLs redirect. The local folder is being renamed from `Projects\Project x Time` to `Projects\Omakase` to match (owner action, done outside a live session). If you find either name, they are the same working copy. After the rename, update the remote: `git remote set-url origin https://github.com/Kejjeh/omakase.git`.

## Tech debt (known, not urgent)

- `name` as the universal join key; `place_id` is captured and nominated as successor (ADR 0004/0006).
- Two parallel path systems: `shared/paths.py` (step scripts) vs. adapter-internal paths (`cuisines/*.py`). Keep in sync when moving files.
- `scripts/add_new_candidates.py` and `scripts/import_italian_research.py` are completed one-off imports — safe to ignore, kept for provenance.
- Excel output bytes churn on every run (openpyxl timestamps) → perpetual dirty `*.xlsx` in `git status`.
- `pandas` is a dependency only for `step1_read_master.py`.
