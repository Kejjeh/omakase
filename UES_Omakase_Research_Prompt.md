# UES Omakase Research Prompt

Paste the prompt below into a Claude or ChatGPT deep research session. It hunts for Upper East Side omakase under $100 and returns structured JSON that can be merged into `scripts/data/omakase/restaurants.json`.

**Why this exists:** the dataset's neighborhood labels used to be hand-typed and disagreed with reality in both directions — Atto Omakase (875 3rd Ave) was labeled `Manhattan (UES)`, One Bite Omakase (411b Amsterdam Ave) was labeled UES while sitting on the Upper West Side, and Uka Omakase (238 E 60th St) was labeled `Manhattan (UWS)` despite genuinely being UES. That is now fixed: neighborhood is derived by point-in-polygon against NYC's 2020 NTA boundaries (see `docs/adr/0003-neighborhood-derived-from-coordinates.md`), so the exclusion list below is trustworthy.

The remaining gap is **coverage**: the dataset only knows about restaurants someone put on the master sheet. This prompt is for finding UES omakase that isn't on it. It demands a **verified street address** for every result so anything found can be checked the same way.

---

## PROMPT (copy everything below this line)

I need you to find **omakase restaurants on the Upper East Side of Manhattan with a base omakase price under $100 per person**, and return structured JSON.

### Geographic definition (strict)

"Upper East Side" means Manhattan, **east of Central Park / 5th Avenue**, between **59th Street and 96th Street**, extending east to the East River. This includes Lenox Hill, Carnegie Hill, and Yorkville.

- A restaurant at 60th St between 2nd and 3rd Ave **counts** (southern edge — flag it as `boundary: true`).
- A restaurant west of 5th Ave **does not count** — that is the Upper West Side.
- A restaurant south of 59th St **does not count** — that is Midtown East.
- A restaurant north of 96th St **does not count** — that is East Harlem.

Do not trust a restaurant's own marketing copy or a directory's neighborhood tag. Many NYC listings label themselves "Upper East Side" for prestige while sitting in Midtown East. **Verify the street address**, and only include the restaurant if the address falls in the box above.

### Price definition

**Base omakase price** = the cheapest seated omakase/tasting counter option, before tax, tip, and drinks. If a restaurant offers tiers (e.g. $85 / $95 / $115), the base price is $85 and it qualifies. Report all tiers. Exclude à la carte sushi restaurants that do not offer an omakase counter.

Include restaurants where the base price is **under $100**. Also include anything between $100–$120 as a near-miss, marked `over_budget: true` — the boundary is soft and I would rather see them than not.

### What to find, per restaurant

1. **Name** as listed on Google Maps
2. **Full street address** (number, street, cross streets if available)
3. **Latitude / longitude** (from Google Maps)
4. **All omakase price tiers** offered, and the base (lowest) price
5. **Number of courses** at the base tier
6. **Google rating** and **review count**
7. **Yelp rating** and **review count**
8. **Infatuation rating** if reviewed (out of 10), else null
9. **Reservation platform** (Resy / OpenTable / Tock / phone / walk-in)
10. **Whether wagyu is included** at the base tier, and any notable premium ingredients (uni, toro, ikura, caviar)
11. **Typical seating duration** if published (e.g. "60 min")
12. **Vibe** — one short phrase: is this an intimate hushed counter, a casual fast-turnover spot, a fusion-heavy scene restaurant?
13. **Whether it is currently open** (verify it has not closed — check for recent reviews within the last 3 months)

### Search strategy

Do not rely on a single source. Please:

- Search Google Maps for "omakase" constrained to the UES box, and also to each sub-neighborhood: Lenox Hill, Carnegie Hill, Yorkville.
- Search along the main commercial avenues specifically: **1st, 2nd, 3rd, Lexington, Madison** between 59th and 96th. Small omakase counters cluster on 1st/2nd Ave and are easy to miss.
- Search Resy and Tock directly, filtered to Upper East Side + Japanese.
- Check The Infatuation's and Eater NY's Upper East Side sushi guides.
- Cross-check any "best cheap omakase NYC" listicles from the last 18 months, then verify each hit's address against the box above.

New/small counters open constantly in this category and often have few reviews. **Include them even if the review count is low** — mark `review_count` honestly and I will weight it myself. Do not filter results by rating; I want coverage, and I will score them.

### Already in my dataset — do not re-report these

These 13 are confirmed Upper East Side by point-in-polygon against NYC's 2020 NTA boundaries (not by anyone's say-so), listed cheapest first:

| Restaurant | Base price | NTA |
|---|---|---|
| Oyishi Sushi | $50 | Yorkville |
| Uka Omakase | $56 | Lenox Hill |
| Sushi Sasabune | $57 | Lenox Hill |
| Noz Market | $90 | Carnegie Hill |
| Akimori | $95 | Carnegie Hill |
| Kissaki | $100 | Lenox Hill |
| Tanoshi Sushi | $102 | Lenox Hill |
| Sushi Goda | $110 | Carnegie Hill |
| Sushi Ishikawa | $135 | Lenox Hill |
| Sushi Jin | $145 | Yorkville |
| Kansha | $145 | Carnegie Hill |
| Kizuna Omakase | $150 | Lenox Hill |
| Kappo Masa | $300 | Carnegie Hill |

So I already have **five** genuinely-UES omakase under $100. I am looking for ones I am missing.

These were labeled UES in my data but are **not** actually UES — they are listed here only so you don't "helpfully" re-suggest them: Atto Omakase (875 3rd Ave, East Midtown), One Bite Omakase (411b Amsterdam Ave, Upper West Side), Tatsuda Omakase, Hanaya Omakase, Sushi Yolo, Sushi Koya, Koete Omakase, Sushi W, Sushi Seki, Tsumo.

If you find fewer than 8 genuinely-UES sub-$100 omakase spots, say so plainly rather than padding the list with Midtown East places — a short honest list is more useful to me than a long wrong one.

### Output format

```json
{
  "restaurants": [
    {
      "name": "Example Omakase",
      "address": "1234 2nd Ave, New York, NY 10021",
      "cross_streets": "between E 64th and E 65th",
      "lat": 40.7654,
      "lng": -73.9601,
      "boundary": false,
      "neighborhood": "Manhattan (UES / Lenox Hill)",
      "price_tiers": [78, 98],
      "min_price": 78,
      "over_budget": false,
      "courses_at_base": 12,
      "google_rating": 4.7,
      "google_review_count": 143,
      "yelp_rating": 4.5,
      "yelp_review_count": 62,
      "infatuation_rating": null,
      "reservation_platform": "Resy",
      "wagyu_at_base": false,
      "premium_ingredients": ["uni", "toro"],
      "pacing": "60",
      "vibe": "Intimate 8-seat counter, quiet.",
      "open": true,
      "last_review_seen": "2026-06",
      "confidence": "high",
      "notes": "Price confirmed on Resy listing; menu page not updated since 2025."
    }
  ],
  "corrections": [
    {
      "name": "Atto Omakase",
      "actual_address": "245 E 51st St, New York, NY 10022",
      "actual_neighborhood": "Manhattan (Midtown East)",
      "is_ues": false
    }
  ],
  "coverage_note": "Searched X sources; found N qualifying restaurants. Areas where I had low confidence: ..."
}
```

### Accuracy rules

- Set `confidence` to `high` only if you verified the price on the restaurant's own site or reservation listing. Use `medium` if from a recent review or article, `low` if inferred.
- If you cannot confirm a price, set `min_price` to null rather than guessing. A null is useful; a wrong number is not.
- If a restaurant appears permanently closed, include it with `"open": false` so I can mark it in my data.
- Prices change often in this category. Note the date of your price source in `notes` where you can.

Take your time and be thorough — accuracy matters more than speed, and address accuracy matters most of all.
