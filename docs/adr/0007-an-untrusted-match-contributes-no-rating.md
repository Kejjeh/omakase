# An untrusted Places match contributes no Reading, not just no derived fields

ADR 0005 and ADR 0006 established that nothing may be derived from a Places match we cannot trust, and `CONTEXT.md` has said since it was written that an untrusted match's "status, coordinates, **rating**" belong to someone else. The code implemented two of the three. `pipeline.score_step` built its reading table straight from `source.read(name)` for every source, with no trust check anywhere, so a wrong match's rating carried its full 0.35 weight into the Composite rating while its `business_status` and coordinates were correctly ignored.

The result was the worst possible shape of the bug: the gate looked present, the tests for it passed, and the one Places field that decides rank was the one field walking through.

**It was not theoretical.** `Bar Tulia` is a Naples, Florida concept with no NYC presence. Places handed it "Tarallucci e Vino NoMad", and it ranked **#15 of 154** on the Italian dashboard on a stranger's reviews. `Olmo` — the only NYC Olmo is a Mexican cantina in Bed-Stuy — carried OLIO E PIÙ East Village's rating to **#6**. `Niku X NYC` sat at **#7 of 198** on omakase. None of the three fired a collision warning, because each wrong listing was claimed by only one row. HANDOFF.md had recorded the defect and deferred it; this is the fix.

## The decision

`score_step` withholds the Google Reading for any Restaurant whose match `shared/places.trust_reason()` rejects. The Reading is not zeroed, floored, or down-weighted — it is **absent**, and the remaining sources renormalize through the code path that already handles a source that never covered the Restaurant. Exclusion is deliberately indistinguishable from absence *to the Scorer*, and deliberately very distinguishable from it *to a reader*.

Three things follow, and each was a choice:

**The Scorer did not change.** Weights, the Wilson bound, the Google 0.97 bias correction and the price exponent are untouched; `scripts/scoring/` still does not know what a place_id is. Trust is a data-quality question about an input, answered upstream, which is why the repair moved no methodology. ADR 0001 stands unmodified.

**Only Google is gated.** The Yelp and Infatuation caches are keyed by *our* name and were filled by a human researching that name; they carry no Places evidence and a wrong Places match is no evidence against them. `pipeline.TRUST_GATED_SOURCES` names the one source that comes from Places. Gating all three would have thrown away good Readings to punish a bad one.

**A Restaurant with no trusted Reading gets no Composite rating at all.** Eleven omakase rows, one Italian and one Philadelphia row were ranked on a single untrusted Google Reading and nothing else; they are now unrated. Not zero, not last — absent, and absent from the percentile cohorts too. The alternative, a floor value, would keep them sortable against restaurants that were actually measured, which is the same lie in a quieter voice.

## Saying so out loud

A silent exclusion is as hard to notice as the silent wrong rating it replaces, and it looks identical to a restaurant no source ever covered. So `trust_reason()` returns *why* — `no_match`, `no_place_id`, `place_id_collision`, or `name_mismatch` — and that reason is carried all the way to the edges:

- `enrich` writes `excluded_sources` (source, reason, a human sentence naming the business Places actually returned, and the rating that was withheld) and a three-valued `google_trusted`.
- `run.py` prints an exclusion count and reason breakdown next to the collision report on every run, and names every Restaurant left with no trusted source.
- The dashboards badge the row `G EXCLUDED` with the reason on hover, badge an unrated row `UNRATED`, and the Excel file gets an `Excluded Sources` column.

An unrated row is also absent from every number a dashboard computes, not just from the ranking: the average rating, the scatter plot and the “Best Value” headline all draw from rows that have a Composite rating. A row with no value score cannot be the best value, and when a filter leaves nothing measured the stat reads `-` rather than naming whichever row happened to be first. The wording is careful for the same reason: the badge legend says the match **could not be verified**, not that it is a different business. `Sottocasa Harlem` at 0.79 is almost certainly the right listing; what the gate knows is that it cannot tell.

`google_trusted` is three-valued on purpose. `True` and `False` are verdicts; `None` means no match exists to judge. Masuda Omakase — operating, but inside another venue with no listing of its own — must not read the same as a wrong-business match. The same distinction keeps `no_match` out of `excluded_sources`: there was no Reading to withhold, so claiming one was withheld would be a second invention.

The raw Google rating, review count and `google_name` **stay on the record** even when excluded. They are the evidence a human needs to rule on the match, and they sit next to the exclusion note rather than in place of it. The adjusted Reading (`google_wilson`) is withdrawn with the rating, so no output can ever show a Google Reading the Composite rating did not use.

## Cautions for whoever revisits this

**The exclusions are not all wrong matches.** The gate rejects `Sottocasa Harlem` vs "Sottocasa Pizzeria Harlem" (0.79) and `Bob & Barbara's` vs "Bob and Barbara's Lounge" (0.71) alongside `Olmo` vs "OLIO E PIÙ East Village" (0.26). That asymmetry is ADR 0005's, not this one's: name similarity fails in both directions, and the threshold sits high because a false *trust* silently corrupts a rank while a false *distrust* loudly loses a Reading. Losing a Reading is the recoverable failure. Do not lower `SIMILARITY_THRESHOLD` to win these rows back — every restaurant it re-admits, it re-admits "Omakase by Teisui" → "Omakase By Tento" (0.76) with it.

**A pin does not currently confer trust, and arguably should.** ADR 0006 makes a pinned `place_id` a deterministic lookup, and `CONTEXT.md` calls a pin an Override — a hand assertion that beats a derived value. Name similarity *is* a derived value, yet it currently overrules the pin: a human could pin `Sottocasa Harlem` to the correct listing and the Reading would still be withheld, because the cached `google_name` still scores 0.79. Every pin in the repo today scores ≥ 0.86 or is a null pin, so making a pin confer trust would change no current output — which is exactly why it was left out of this repair rather than smuggled into it. It is the obvious remedy for the rows above and it needs an owner's ruling, not an agent's.

**Never re-add an excluded Reading downstream.** The point of nulling `google_wilson` in the same step that records the exclusion is that the record cannot disagree with itself. `score_step` and `enrich` take the *same* trust callable for the same reason.
