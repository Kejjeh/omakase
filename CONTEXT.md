# Omakase

A data pipeline that ranks NYC restaurants per cuisine by blending ratings from multiple sources, adjusting for review-count uncertainty and price, and publishing a per-cuisine dashboard.

## Language

**Restaurant**:
A single NYC establishment we score. Identified by `name` (the join key everywhere).
_Avoid_: place, spot, venue.

**Cuisine**:
A top-level partition of the dataset (currently `omakase`, `italian`). Each cuisine has its own master sheet, ratings caches, scored output, and dashboard. Restaurants do not move between cuisines.
_Avoid_: category, genre, type.

**Rating source**:
An external provider of a numeric rating + review count for a restaurant. Three exist today: Google Maps, Yelp, The Infatuation. Each source has its own raw scale, freshness story, and trust weight.
_Avoid_: provider, site, platform.

**Region**:
A city's neighborhood boundary set, plus the property names it is keyed by (`scripts/shared/geo.py`). Each Cuisine is scoped to at most one Region: `omakase` and `italian` use NYC's 2020 NTA boundaries; the Philadelphia cuisines (`philly`, `kensington`) have none yet and derive nothing.
_Avoid_: city, map, boundaries.

**Derived neighborhood**:
Where a Restaurant actually is, resolved by point-in-polygon of its coordinates against its Cuisine's Region. Stored as structured parts — `borough`, `nta_code`, `nta_name` — and composed into a display string at the edges (dashboard, Excel), never stored pre-composed. This is the only neighborhood anything is allowed to filter on. See ADR 0003.
_Avoid_: neighborhood (ambiguous — say which), hood, area.

**Raw neighborhood**:
The hand-typed label from the Master sheet (or an Italian research file), preserved as `neighborhood_raw`. Reference only. It was wrong in both directions often enough that it is never filtered on and never displayed without an `(unverified)` marker.
_Avoid_: the neighborhood, the real neighborhood.

**Trusted match**:
Whether a Restaurant's Google Places result actually describes that Restaurant (`scripts/shared/places.py`). Places substitutes a similarly-named operating business when a Restaurant has closed, so an untrusted match's fields — status, coordinates, rating — belong to someone else. Requires a `place_id`, no `place_id` collision with another Restaurant, and a name similarity ≥ 0.80. Nothing is derived from an untrusted match.
_Avoid_: good match, valid match, verified.

**Override**:
A deliberate hand assertion that beats a derived value — `closed_override`, and a pinned `place_id`. Distinct from an absent value: `None` means nobody has ruled, which is what a defaulted `closed: False` always really meant. Overrides exist so external data can be overruled without arguing with the pipeline — see ADR 0005 and ADR 0006.
_Avoid_: manual flag, hardcoded value.

**Pin**:
A hand-set `place_id` in `scripts/data/<cuisine>/place_id_overrides.json` that makes a Restaurant's Google lookup deterministic — fetched by id rather than searched by name, so it cannot drift to another business. A null pin asserts the Restaurant has no Google listing at all and must not be searched (Masa, which sits next door to Bar Masa). Every pin carries a note; a test enforces it. See ADR 0006.
_Avoid_: hardcoded id, mapping.

**Collision**:
Two Restaurants carrying the same `place_id`. Proof that at least one is matched to the wrong business, and a far better signal than name similarity. Reported on every pipeline run; `run.py --strict` exits non-zero on one.
_Avoid_: duplicate, conflict.

**Reading**:
What a single Rating source returns for a single Restaurant — at minimum a rating and a review count. A Restaurant can have a Reading from zero, one, two, or three sources.
_Avoid_: data point, record, score (score means something else).

**Composite rating**:
A weighted blend of adjusted Readings, on a 1–5 scale. Weights: Google 0.35, Yelp 0.45, Infatuation 0.20, renormalized when a source has no Reading. "Adjusted" means: Google ratings are bias-corrected (×0.97) and then Wilson-lower-bounded; Yelp ratings are Wilson-lower-bounded; Infatuation 1–10 editorial ratings are linearly rescaled to 1–5.
_Avoid_: average rating, mean rating, blended score.

**Value score**:
The Composite rating discounted by price: `composite × (100 / min_price) ** β`, where β is the price exponent (either fixed in config or fit empirically by log-log regression across the cuisine).
_Avoid_: bang-for-buck, adjusted score.

**Specialty**:
Cuisine-specific facets of a Restaurant that don't come from a Rating source — e.g. for omakase: wagyu availability, AYCE format; for italian: pasta program, pizza program, Michelin status. Sourced from hand-curated research files, not the API/scraper pipeline.
_Avoid_: features, attributes, tags.

**Master sheet**:
The hand-maintained Excel file (`scripts/data/<cuisine>/master.xlsx`) that defines which Restaurants exist for a given Cuisine. Source of truth for inclusion.
_Avoid_: spreadsheet, input file, list.

**Dashboard**:
The per-Cuisine static HTML page (`docs/<cuisine>/index.html`) that visualizes the scored Restaurants. Currently carries its data inline as a JS literal.
_Avoid_: page, site, report.

## Example dialogue

> **Dev**: Should the Scorer call sources directly?
>
> **Domain**: No — the Scorer just blends Readings into a Composite rating and a Value score. Fetching Readings from each Rating source is upstream of it.
>
> **Dev**: What if a Restaurant has no Reading from Infatuation?
>
> **Domain**: Then the Composite rating renormalizes over Google and Yelp only — Infatuation's 0.20 weight gets redistributed. We never drop a Restaurant just because Infatuation hasn't covered it.
>
> **Dev**: And wagyu availability? That's not a Reading?
>
> **Domain**: Right — wagyu is a Specialty. Specialties live in research files and get merged onto a Restaurant after scoring. They don't affect the Composite rating.
