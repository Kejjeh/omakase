# Every cuisine states its own Places search terms; there is no default

`step2_fetch_ratings.py` built its Google Places query as `f"{name} {SEARCH_TYPE} {neighborhood} {SEARCH_CITY}"`, where both terms came from a single ternary:

```python
SEARCH_CITY = "Philadelphia" if CUISINE == "philly" else "New York City"
SEARCH_TYPE = "happy hour bar" if CUISINE == "philly" else "sushi"
```

That reads as "philly is the special case," but what it actually means is "every cuisine that is not philly is omakase." It was correct when omakase and philly were the only two cuisines and silently wrong for every cuisine added afterwards. Italian restaurants were searched as `"Lupa italian restaurant..."` → no: as `"Lupa sushi Manhattan (Greenwich Village) New York City"`, and Places dutifully returned sushi restaurants. Lupa matched "Shin Takumi Omakase"; Quality Italian matched "Sushi of Gari 46"; Sottocasa Greenpoint matched "Matsuzuki Sakura" in Long Island City. 24 of 154 Italian restaurants held another restaurant's rating **and** coordinates. Kensington is in Philadelphia but is not named `philly`, so its restaurants were searched in New York.

Search terms now live in an explicit `SEARCH_CONFIG` dict keyed by cuisine, and a cuisine with no entry raises rather than inheriting anything. Re-fetching Italian with `italian restaurant` fixed 16 of the 24 bad matches.

Two things to keep in mind:

**A bad match is invisible per-entry.** The cached record is well-formed — it has a rating, a review count, a name, coordinates. Nothing about it looks broken; it simply describes a different restaurant. This is why `--repair` (which re-fetches entries missing location fields) could not fix it and `--force` exists: when the *query* changes, every cached entry is suspect regardless of its shape.

**Three Italian restaurants are still mismatched** — Bar Tulia, Lodi, and Olmo. Lodi and Olmo both resolve to `OLIO E PIÙ East Village`, which is why duplicate `place_id` is the check worth running: it catches what name similarity cannot. Lodi's bogus match moved it from #136 to #2 on composite rating, so these are not cosmetic.

The deeper issue is that Restaurant is keyed by `name` (see CONTEXT.md), and a name is not a stable identifier — it cannot distinguish Trattoria L'Incontro in Astoria from L'incontro by Rocco on the Upper East Side. `place_id` is now captured and is the better join key if this keeps biting.
