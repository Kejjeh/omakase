# Decision log

Settled decisions. Do not re-litigate any of these without new evidence; each cost real debugging to reach. Items marked **(inferred)** were reconstructed from code and git history rather than found stated.

## Documented in ADRs (read the ADR before touching the area)

| # | Decision | Rejected alternative |
|---|---|---|
| [0001](adr/0001-weighted-composite-blend.md) | Composite = weighted blend G .35 / Y .45 / I .20, renormalized when a source is missing | Equal mean (the old shipped behavior — looks like the "original" in git blame; it was the bug) |
| [0002](adr/0002-dashboard-fetches-data-json.md) | Dashboard fetches `data.json` at runtime; view over http:// only | Regex-rewriting an inline JS data blob (fragile; implicit schema). Do not re-inline to "fix" file:// |
| [0003](adr/0003-neighborhood-derived-from-coordinates.md) | Neighborhood derived by point-in-polygon from Places coordinates; hand label kept as `neighborhood_raw`, display-only | Trusting the hand-typed label (wrong in both directions); a standalone geocoding step (Places already returns coordinates) |
| [0004](adr/0004-search-terms-are-per-cuisine.md) | Every cuisine states its own Places search terms; missing entry raises | A ternary defaulting non-philly cuisines to "sushi"/NYC (gave 24 Italian restaurants another restaurant's rating) |
| [0005](adr/0005-closed-is-derived-with-an-explicit-override.md) | `closed` derived from `business_status` only when no hand assertion exists; `closed_override` always wins; temporary closure is a separate field | Overwriting with Google's status (would have wrongly reopened 7 closed restaurants whose Places match was a substitute business) |
| [0006](adr/0006-place-id-is-the-google-join-key.md) | Google matches pinnable by `place_id` (null = "don't search"); collisions reported every run, fatal under `--strict` | Trusting name search; name-similarity-only validation (fails in both directions) |

## Not in ADRs

- **Wilson score lower bound (z=1.96) as the rating adjustment**, mapping the 1–5 scale to a proportion and back. Rewards high review counts conservatively. A Bayesian/IMDB-style prior exists as a config option but Wilson is the shipped default. (inferred from `config.py` and `sources/__init__.py`)
- **Google ratings ×0.97 bias correction before Wilson**, compensating Google's inflation relative to Yelp. Constant lives in `scripts/sources/__init__.py`. (stated in config comments)
- **Value score = composite × (100/price)^β, β fit per cuisine** by log-log regression, clamped to [0.1, 0.6], fallback 0.3 with <5 price pairs. Fixed β is available via config. (inferred from `scripts/scoring/`)
- **Yelp is refreshed by human deep-research, not an API or scraper.** The research prompts (`Yelp_Research_Prompt*.md`) are the fetcher. Presumably chosen over the Yelp Fusion API for cost/robot-blocking reasons. (inferred)
- **All caches and generated outputs are committed to git.** Makes the pipeline runnable offline and diffs reviewable; the price is xlsx binary churn. (inferred)
- **No compiled geo stack** — hand-rolled ray casting over a vendored GeoJSON instead of shapely, ~30 lines for a few hundred points. (stated in `shared/geo.py`)
- **`name` is the join key everywhere** despite its known weakness; `place_id` was captured as the escape hatch and ADR 0006 nominates it as the better key if name keeps biting. Not yet migrated. (stated in CONTEXT.md / ADR 0004)
- **Refreshing is separated from scoring**: `RatingSource.refresh()` raises `NotImplementedError` on purpose; the step scripts own network I/O so `run.py` is always offline, fast, and deterministic. (stated in `pipeline.py` docstring)
- **Duplicate master-sheet rows are surfaced, not auto-deleted.** Removing a row is a heavier act than pinning; the 3 omakase collision groups are left for a human. (stated in ADR 0006)
