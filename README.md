# NYC Omakase Finder

A data-driven ranking of 149 NYC omakase and sushi restaurants, powered by multi-source ratings from Google Maps, Yelp, and The Infatuation.

## Live Site

👉 **[View the interactive chart](https://YOUR_USERNAME.github.io/omakase/)** ← Update after enabling GitHub Pages

## Methodology

Composite ratings are built from up to 3 sources:

| Source | Weight | Treatment |
|--------|--------|-----------|
| Google Maps | 35% | Wilson Score Lower Bound (z=1.96) × 0.97 bias correction |
| Yelp | 45% | Wilson Score Lower Bound (z=1.96) |
| The Infatuation | 20% | Editorial 1-10 → normalized to 1-5 scale |

Weights are renormalized when fewer sources are available (e.g., a 2-source restaurant uses the two available weights summing to 1).

**Value Score** = Composite Rating adjusted by price (log-log regression, empirically derived exponent β=0.100).

## Project Structure

```
├── docs/index.html              # GitHub Pages interactive site
├── scripts/
│   ├── config.example.py        # Copy to config.py, add your API key
│   ├── restaurants.json          # Master restaurant list
│   ├── ratings_cache.json        # Google Maps ratings cache
│   ├── yelp_cache.json           # Yelp ratings (136/149 found)
│   ├── infatuation_cache.json    # Infatuation ratings (49/149 found)
│   ├── scored_restaurants.json   # Final computed scores
│   ├── step1_read_master.py      # Parse master spreadsheet
│   ├── step2_fetch_ratings.py    # Google Places API fetcher
│   ├── step2b_fetch_infatuation.py # Infatuation web scraper
│   ├── step3_compute_scores.py   # Composite scoring engine
│   └── step4_generate_output.py  # Excel output generator
├── Omakase_Ratings.xlsx          # Generated ratings spreadsheet
└── Yelp_Research_Prompt.md       # Prompt for AI deep research (Yelp data)
```

## Setup

```bash
cd scripts
cp config.example.py config.py
# Edit config.py with your Google Places API key
pip install requests beautifulsoup4 openpyxl
python run_all.py
```

## GitHub Pages

Enable Pages in repo Settings → Pages → Source: "Deploy from a branch" → Branch: `main`, folder: `/docs`.
