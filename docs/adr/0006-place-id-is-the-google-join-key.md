# A Google match can be pinned by `place_id`, and a shared `place_id` fails loudly

Restaurant is keyed by `name` (see CONTEXT.md), and the pipeline asked Google Places for a restaurant by searching that name. A name is not a stable identifier. When a restaurant closes, is renamed, or shares a name with a sibling location, Text Search does not return nothing — it quietly returns a *different, operating* business. The cached record then looks perfectly well-formed: a rating, a review count, coordinates, an address. It simply describes someone else.

Nine such matches were found in the omakase dataset and one in Italian, by noticing that two rows had ended up with the same `place_id`. That is proof rather than inference: one listing cannot be two restaurants. It is also a much better detector than name similarity, which fails in both directions — "Mario's" vs "Mario's Restaurant of Arthur Avenue" is a correct match that scores badly, while "Omakase by Teisui" vs "Omakase By Tento" is a wrong match that scores well.

The damage was not cosmetic. Lodi carried OLIO E PIÙ's rating and sat at #2 on composite; pinned to its own listing it is 3.93 and permanently closed. Robataya (closed 2017) carried Sushi by Bou's rating. Every wrong match also hands over coordinates, and therefore the derived neighborhood from ADR 0003.

Two mechanisms now exist.

**Pinning.** `scripts/data/<cuisine>/place_id_overrides.json` maps a restaurant name to a `place_id`. When one is present, `step2_fetch_ratings.py` calls the Place **Details** API by id instead of searching by name. A lookup by id is deterministic and cannot drift. Pins live in JSON rather than the master sheet — `master.xlsx` is binary, and a pinned id that cannot be read in a diff cannot be reviewed. Every pin carries a `note`; a test enforces it, because a bare id is indistinguishable from a guess.

A pin may be `null`, meaning "this restaurant has no Google listing of its own; do not search". That is its own kind of correction and the subtler half of the mechanism. **Masa** is an operating three-Michelin restaurant with no Places listing, so a name search lands on Bar Masa next door. Without a way to say *stop looking*, the pair re-collides on every fetch. A null pin also clears whatever wrong business was previously cached, since leaving it would preserve the collision.

**Loud failure.** `scripts/run.py` reports collisions on every run and exits non-zero under `--strict` (for CI); `step2_fetch_ratings.py` reports them at fetch time. Previously this required someone to remember to run an ad-hoc script.

Three cautions for whoever works on this next.

**A wrong match is not evidence of closure.** An automated pass proposed marking Masa closed because Places could not find it. Absence from Places means absence from Places. This is the same trap as ADR 0005 and the reason `closed_override` beats derivation; there is now a regression test pinning Masa open specifically.

**Some rows are not restaurants we want.** Research passes introduced rows that do not belong: "Bar Tulia" is a Naples, Florida concept with no NYC presence, and the only "Olmo" in New York is a Mexican cantina in Bed-Stuy, not a Manhattan Italian restaurant. Others are duplicates of a row that already exists — "Sushi Hayashi (Williamsburg)" is the same 225 Grand St restaurant as "Sushi Hayashi", and "Hiyake Omakase (Bowery)" is the former name of the business now listed as Gyu-Ichiro at 135 Bowery. Removing a row edits the master sheet, which is a heavier and less reversible act than pinning an id, so these are surfaced for a human rather than resolved automatically.

**Search terms are part of the join.** ADR 0004 covers this, but the two interact: a wrong `SEARCH_TYPE` produces wrong matches wholesale, and pinning is the remedy of last resort, not a substitute for asking the right question. Kensington's restaurants were being searched in New York; correcting the config and re-fetching fixed all seven of its bad matches with no pins needed.
