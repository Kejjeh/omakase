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
