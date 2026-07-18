# `closed` is derived from Google, with an explicit hand override that always wins

`closed` was a hand-maintained boolean, and it had drifted: Google reported 20 omakase and 8 Italian restaurants whose status contradicted it. That looks like the same bug as the neighborhood labels, and the obvious fix — overwrite `closed` with `business_status` — is wrong. Two findings changed the design.

**Most "open" values were never a decision.** Only 12 restaurants ever asserted `closed: True`, all in `research_input/omakase/specialties_151.json`. Every other value came from `rec.setdefault("closed", False)` in the pipeline, which means "nobody said", not "someone checked and it's open". Google's status is new information there, not a contradiction, so there is nothing to overrule.

**Where a human *had* decided, the human was right and Google was wrong.** All 7 restaurants where Google said OPERATIONAL but a research file said closed turned out to have a wrong Places match — and that is not a coincidence, it is the mechanism. The restaurant shut, Text Search could no longer find it, and it silently returned a similarly-named operating business instead: ROKI matched "RokuNana", Robataya matched "Sushi By Bou - East Village", Sushi Yugen matched "YUGIN". The OPERATIONAL status described the substitute. Overwriting would have reopened all seven.

So `closed` is now derived from `business_status` **only when no explicit assertion exists**, and an assertion is preserved as `closed_override` and always wins. The two meanings that used to share one field are now separate: `closed_override is None` means nobody has ruled, which is what the old `False` mostly meant.

Anything derived from a Places field is gated on `scripts/shared/places.is_trustworthy`, because a wrong match's fields describe the wrong business. Trust needs a `place_id`, no `place_id` collision with another restaurant, and a name similarity ≥ 0.80. That threshold is calibrated against "Omakase by Teisui" vs "Omakase By Tento" — a genuinely different restaurant scoring 0.76 — so it must stay above that. Raising it only makes the pipeline defer to hand values more, which is the safe direction.

Temporary closures get their own field. `CLOSED_TEMPORARILY` sets `temporarily_closed`, not `closed`: a restaurant that is dark this month is not the same as one that is gone, and the dashboards style them differently (a distinct badge, a lighter row dim, and not hidden by "hide closed").

Two cautions for whoever revisits this:

**Google is not an oracle.** It reports Lupa as CLOSED_PERMANENTLY while Yelp and the Michelin Guide both say *temporarily* closed. Lupa was adopted as closed because nothing overrode it, but if you find a case like this, the fix is to assert `closed: false` in the research file — an override exists precisely so external data can be overruled without arguing with the pipeline.

**A restaurant Places cannot find is not necessarily closed.** Masuda Omakase has no `place_id` at all; it is an operating kosher omakase at 1385 Broadway that runs inside another venue and has no standalone listing. Untrusted and unfound both derive nothing, leaving `closed` false, which is the right default.
