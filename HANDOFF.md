# Handoff — state of play (2026-09-17)

Read `CLAUDE.md` first (commands, gotchas, model routing). This file is what's done, what's broken, and what to do next.

## Done and working

- Full pipeline for all 4 cuisines: `python scripts/run.py --all` completes in seconds; regenerates scored JSON, dashboard `data.json`, and root Excel files. Verified 2026-09-01.
- Test suite: `python -m pytest tests/ -q` → **240 passed, 6 skipped, ~2.7s** (skips are data-conditional: philly/kensington have no override/closure files). Verified 2026-11-07.
- Omakase (199 rows) and Italian (152 rows) dashboards: `docs/omakase/`, `docs/italian/`, linked from the `docs/index.html` landing page, served via GitHub Pages.
- Neighborhood derivation (NYC), trust-gated closure logic, place_id pinning (17 omakase pins, 2 italian), collision reporting — all covered by ADRs 0003–0006 and tests.
- **Trust-gated Readings (ADR 0007, 2026-09-17).** An untrusted Google match no longer contributes its rating to the Composite rating. Was known bug 2 below; now fixed, tested and documented.

## In progress / half-finished

- **Philly + Kensington cuisines are data-only.** They score and write `docs/<cuisine>/data.json` but have **no `index.html` dashboard** and are not linked from the landing page. Their `yelp_cache.json` files are empty (`{}`), so they score on Google + Infatuation only. No Philadelphia neighborhood boundary set is registered (`cities.PHILADELPHIA.region = None`), so their hand-typed neighborhoods pass through unverified.
- ~~**3 omakase place_id collision groups.**~~ **Resolved 2026-11-07** on the owner's ruling; `--strict` now exits 0. Only **two** were duplicates, and neither needed a master.xlsx edit — both were preserved extras living only in `restaurants.json`: "Hiyake Omakase (Bowery)" (the former name of Gyu-Ichiro, 135 Bowery) and "Sushi Hayashi (Williamsburg)" (the same 225 Grand St restaurant as Sushi Hayashi) were deleted, keeping the row the pin already named. The third was **not** a duplicate: "Unique Omakase" is a distinct restaurant that was at 120 1st Ave and has since closed, and Places had no listing for it, so a name search fell through to its neighbour "Omakase Sushi by No name" (which `Omakase by No Name` legitimately owns). It is now pinned `null` with an asserted closure, and still scores on its own Yelp reading.

## Known bugs

1. ~~**Two Italian rows still exist for businesses we don't want.**~~ **Fixed 2026-11-07** on the owner's ruling. Both re-verified before deletion: **Bar Tulia** has exactly two locations, 462 5th Ave S and 9118 Strada Pl, both in Naples, Florida — the `305 W 39th St` in the row was never a Bar Tulia address. **Olmo** in New York is a Mexican restaurant at 103 Saratoga Ave, Bedford-Stuyvesant (Bib Gourmand); there is no NYC Italian Olmo, and the Infatuation 7.8 the row ranked on at #85 describes the Mexican one, so that was a wrong-business Reading too, not a salvageable source. Rows and their entries removed from `restaurants.json`, `ratings_cache.json`, `infatuation_cache.json`, `user_state.json` and `research_input/italian/discovery.json`. `import_italian_research.py` rewrites `restaurants.json` wholesale, so it now carries an `EXCLUDED_NAMES` set pinned by a regression test in `tests/shared/test_overrides.py` — otherwise a re-import would silently resurrect them.
2. ~~Untrusted Google matches still contribute their rating to the composite.~~ **Fixed 2026-09-17, ADR 0007.**
3. ~~`run.py --all --strict` exits non-zero.~~ **Fixed 2026-11-07** by resolving the 3 collision groups; it exits 0 and is now the standard check. It was never weakened to accommodate ADR 0007.
4. ~~`scripts/data/omakase/master.xlsx` cannot be opened.~~ **Fixed 2026-11-07.** It was a truncated zip: valid local headers for all 12 members, but the central directory was cut off 24 bytes in and there was no end-of-central-directory record, so `openpyxl`, `pandas` and `unzip` all refused it and `step1_read_master.py` died with `BadZipFile`. The archive was rebuilt from its members (every CRC valid, no member data missing), so no content was reconstructed or guessed. It had been truncated in **every** commit since `fc2d1b7` (2026-05-04) — byte-identical throughout — which is why the omakase P0 below had never actually been runnable. Not a line-ending fault: CRLF mangling corrupts deflate streams and all CRCs passed. `.gitattributes` now marks `*.xlsx binary` so no eol filter can reach it. The sheet holds 164 rows / 162 named restaurants.

## Prioritized next steps (each ≈ one Sonnet session unless marked Opus)

- ~~**P0 — Resolve the bad Italian rows.**~~ **Done 2026-11-07.** Italian is now 152 rows and **every one of them scores** — the cuisine has no unrated rows left, and its exclusions fell from 8 to 6.
- ~~**P0 — Resolve the 3 omakase duplicate rows.**~~ **Done 2026-11-07.** The owner ruled that agents may remove rows (Open question 1). `run.py --all --strict` exits 0. **The documented remedy turned out to be the wrong one** and was not used: neither duplicate row is on the master sheet (`master.xlsx` holds `Omakase by No Name`, `Unique Omakase` and `Sushi Hayashi`, but not `Hiyake Omakase (Bowery)`, `Gyu-Ichiro` or `Sushi Hayashi (Williamsburg)`), so editing the sheet and re-running step1 would have left both duplicates in place as preserved extras while adding ~16 unrelated rows. They were removed from `restaurants.json` and the Google/Infatuation caches directly. Side effect worth knowing: the 6 `place_id_collision` exclusions are gone, so Gyu-Ichiro (3.69) and Sushi Hayashi (4.39) now carry their trusted Google readings instead of being unrated, and Omakase by No Name gained Google alongside Yelp.
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

> **Superseded 2026-11-07.** Resolving the 3 omakase collision groups removed all 6 `place_id_collision` exclusions, and removing the two
> invented Italian rows took italian from 8 exclusions / 1 unrated to 6 / 0. Totals are now **26** withheld Readings and **8** rows with no
> trusted source: omakase 18 / 7, italian 6 / 0, philly 2 / 1, kensington 0 / 0. The table above is kept as the record of what ADR 0007 did.

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

## Dashboard usability pass (2026-09-19)

Seven defects reproduced in a real browser (Chromium via Playwright, both
dashboards, desktop 1280px and phone 390px) and repaired. Presentation only:
`docs/omakase/index.html` and `docs/italian/index.html` carry identical edits,
and `run.py --all` reproduced every committed `data.json` and
`scored_restaurants.json` byte-for-byte (only the usual `.xlsx` churn). No
threshold, pin, row, weight or ranking order moved — the default view of both
dashboards shows the same count, average, and Best Value as before.

| # | Defect | Repair |
|---|---|---|
| 1 | **A failed Chart.js load emptied the whole report.** The library comes from a CDN; when it did not arrive, `new Chart(...)` threw inside `applyFilters()` *before* `updateTable()` ran. Measured with the CDN blocked: stat cards read "150 restaurants, 4.20 avg" above **0 table rows**, and every filter change kept it at 0. | `updateTable()` now runs before `updateChart()`, and `updateChart()` returns a placeholder instead of throwing. With Chart.js blocked both dashboards now render all 150/145 rows and zero page errors. |
| 2 | **Filters matching nothing left a bare table.** Indistinguishable from defect 1 or a failed data load. | An empty result renders one full-width row: "No restaurants match these filters", naming the filters most likely responsible. |
| 3 | **Max Price 0 meant "no maximum".** `parseFloat(v) \|\| 9999` turned a typed 0 falsy. Typing 0 on omakase *widened* the table from 150 to 163 rows. | An empty box means no bound; a typed 0 means zero. Max Price 0 now yields 0 rows. |
| 4 | **An unknown price was treated as $0.** `r.min_price \|\| 0` let the two price-less omakase rows (ROKI, Tokyo Bar — `price_str: "Unlisted"`) pass *any* maximum: both appeared under "Max Price 30" showing `$?`. | A row with no price cannot be shown to sit inside a price range, so a price bound excludes it — the rule the walk-time filter already used for an unknown walk time. |
| 5 | **"Avg Price" showed `$0` when nothing filtered had a price.** Reachable in two steps (neighborhood *Upper West Side (Central)* + Max Price 1 left only Tokyo Bar): the card read `$0`, i.e. free. | Reads `-`, like the other cards already did. |
| 6 | **Sorting was mouse-only.** No `<th>` could take focus (Tab skipped the table entirely), so a keyboard user was stuck with the default ordering. | Headers are focusable, respond to Enter and Space, carry `aria-sort`, and show a focus ring. Verified: Enter sorts price descending ($195, $188, $180), Space ascending ($24, $30, $30). |
| 7 | **The page scrolled sideways on a phone.** A `<select>` is as wide as its longest option ("Brooklyn (Bath Beach)"), which stretched the grid track: at 390px the document was 466px wide on omakase and 582px on italian. | `min-width: 0` on the filter groups. Both dashboards now measure exactly 390px at 390px. |

One deliberate visibility addition, not a defect fix: the Avg Composite card
gains a note reading "over 150 of 161 rated" whenever the filtered set holds
rows whose rating was withheld (ADR 0007). The count card includes them and the
average cannot, and nothing on the page said so.

**Behavior change worth knowing:** with *Hide closed → Show all*, ROKI and Tokyo
Bar no longer appear under omakase's default Max Price of 200, because their
price is unknown and an unknown price no longer satisfies a bound. Clear the Max
Price box to see them.

Tests: `tests/dashboard/test_dashboard_filters.py` (30 cases) plus 6 added to
`test_dashboard_stats.py`, with the node harness factored into
`tests/dashboard/jsharness.py`. 28 of the 30 new filter cases fail against the
pre-fix HTML; the 2 that pass either way are the must-not-regress guards.
`232 passed, 4 skipped`.

Not fixed, deliberately: the chart's y-axis is hardcoded to 3.0–5.0. No current
row scores below 3.148, so nothing is clipped today — worth a look only if a
lower-rated row ever lands.

Checked and found sound, so left alone: back navigation (landing → dashboard →
filter → back → forward restores the filter *and* the matching row count), the
withheld-rating badges and their hover text, the UNRATED badge, the legend
wording, and the empty-result stat cards, which already read `-`.

Commits on `claude/epic-ramanujan-mojj88`, off `main` at 0ab4bd6:

- `3075ce2` Repair seven dashboard defects found by driving the released pages
- `2271bc9` Cover the filter, empty-state and chart-failure paths
- `a2ec259` Record the dashboard usability pass

PR: https://github.com/Kejjeh/omakase/pull/2 — **merged 2026-11-07.** It was opened
for Astra's independent review, which did not happen. It was verified instead
by running the full suite (Python, plus the dashboard JavaScript under node) on
the PR merged into current main with outbound network blocked, and by checking
that `run.py --all` still reproduces every committed `data.json` byte-for-byte.

## Open questions (owner input needed)

1. ~~May agents remove rows?~~ **Answered and fully discharged 2026-11-07: yes, with the owner's explicit approval per removal.** It means "owner approves an agent doing it", not "owner does it". All four rows the question named are gone — the 2 omakase duplicates, then `Bar Tulia` and `Olmo` under a separate approval. Re-verify a row before deleting it: of the three omakase groups put forward as duplicates, one turned out not to be, so approval to remove is not a finding that the row is wrong.
2. Are `philly`/`kensington` still active goals, or parked? (Chose conservatively to document them as in-progress, not dead.)
3. Are `scripts/build_top12.js`, `build_top15.js`, and `final_docs/*.docx` still wanted? They're one-off docx generators with hardcoded data, stale relative to current scores. Left untouched.
4. The Google Places API key in the gitignored `scripts/config.py` — verified never committed to git history. Consider restricting/rotating it anyway since it predates this audit.
5. **Should a pin confer trust?** ADR 0006 makes a pinned `place_id` deterministic and GLOSSARY.md calls a pin an Override — a hand assertion that beats a derived value. Name similarity *is* a derived value, but it currently overrules the pin, so pinning `Sottocasa Harlem` to the correct listing would **not** bring its Reading back. Every pin in the repo today scores ≥ 0.86 or is a null pin, so the change would alter no current output; it was deliberately left out of ADR 0007 rather than smuggled in. Ruling yes gives the table above a one-pin-each remedy. Ruling no means those rows stay unrated until the rows or the threshold change — and the threshold must not move (ADR 0007, cautions).

## Housekeeping

- The GitHub repo was renamed to `Kejjeh/omakase`; old remote URLs redirect. The local folder was renamed from `Projects\Project x Time` to `Projects\Omakase` to match, and the remote was repointed to `https://github.com/Kejjeh/omakase.git` — both done 2026-11-07. The old remote URL also had the owner/repo casing wrong (`kejjeh/Omakase`) and worked only via GitHub's redirect. Older notes, and Claude session history, may still say `Project x Time`: same working copy.
- Tag `archive/omakase-experiments-20260504` preserves a four-commit experiment lineage from 2026-05-04 that is reachable from no branch: `a645460` (price exponent 0.05) → `c5f3a61` (Yelp 50/Google 30/Infatuation 20) → `6241e70` (4/5/6 subway proximity) → `14cf3f9` (initial pipeline). It was pushed to rescue those commits from stale local clones (`Desktop\Projects\Omakase` and five nested copies) before they were deleted on 2026-11-07. Nothing depends on the tag; the subway work is already in the current code, and the weighting and exponent values were deliberately superseded. Do not build on it — it exists only so the experiments stay recoverable.

## Tech debt (known, not urgent)

- `name` as the universal join key; `place_id` is captured and nominated as successor (ADR 0004/0006).
- Two parallel path systems: `shared/paths.py` (step scripts) vs. adapter-internal paths (`cuisines/*.py`). Keep in sync when moving files.
- `scripts/add_new_candidates.py` and `scripts/import_italian_research.py` are completed one-off imports — safe to ignore, kept for provenance.
- Excel output bytes churn on every run (openpyxl timestamps) → perpetual dirty `*.xlsx` in `git status`.
- `pandas` is a dependency only for `step1_read_master.py`.
