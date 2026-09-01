# The Restaurant Report

Data-driven restaurant rankings per cuisine — currently NYC omakase (201 restaurants) and NYC Italian (154), with Philadelphia datasets in progress — blending Google Maps, Yelp, and The Infatuation ratings into a composite score and a price-adjusted value score.

**Live dashboards:** https://kejjeh.github.io/omakase/

## Methodology (short version)

| Source | Weight | Treatment |
|--------|--------|-----------|
| Google Maps | 35% | ×0.97 bias correction, then Wilson score lower bound (z=1.96) |
| Yelp | 45% | Wilson score lower bound (z=1.96) |
| The Infatuation | 20% | Editorial 1–10 rescaled to 1–5 |

Weights renormalize when a source hasn't covered a restaurant. **Value score** = composite × (100/price)^β, with β fit per cuisine by log-log regression. Neighborhoods are derived from coordinates (point-in-polygon against NYC NTA boundaries), not trusted from hand-typed labels. Full rationale lives in `docs/adr/`.

## Setup and running

```bash
pip install -r requirements.txt
python -m pytest tests/ -q          # sanity check
python scripts/run.py --all         # rebuild scores, dashboards, Excel files
python -m http.server -d docs 8000  # view dashboards locally (file:// won't work)
```

Refreshing source data needs a Google Places API key in `scripts/config.py` (copy `scripts/config.example.py`; the file is gitignored — never commit it).

## Where things live

For agents: **`CLAUDE.md` is the source of truth** (commands, conventions, gotchas), with current status in `HANDOFF.md`. For structure: `docs/ARCHITECTURE.md`. Domain vocabulary: `CONTEXT.md`. Settled decisions: `docs/DECISIONS.md` and `docs/adr/`.
