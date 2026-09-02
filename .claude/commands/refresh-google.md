---
description: Refresh the Google Places ratings cache for one cuisine
argument-hint: <cuisine: omakase|italian|philly|kensington>
---

Refresh the Google ratings cache for cuisine `$ARGUMENTS` (default: omakase). This spends API quota — be deliberate.

1. Confirm `scripts/config.py` exists (it is gitignored and holds the API key). If missing, stop and tell the user to copy `scripts/config.example.py` and add their key. Never print, commit, or copy the key anywhere.
2. Dry-run first: `set PYTHONUTF8=1` then `python scripts/step2_fetch_ratings.py --cuisine $ARGUMENTS --dry-run` and report how many fetches it would do.
3. If the count is reasonable (normal run only fetches uncached rows), run it without `--dry-run`. Use `--repair` only for entries missing lat/lng fields; use `--force` ONLY if the user confirms — it re-fetches everything.
4. After fetching, watch the collision report it prints. A new collision means a wrong match — record it in HANDOFF.md rather than guessing a fix; the fix is usually a pin in `scripts/data/$ARGUMENTS/place_id_overrides.json` (every pin needs a researched `note` — see docs/adr/0006).
5. Rebuild: `python scripts/run.py --cuisine $ARGUMENTS`, then `python -m pytest tests/ -q`.
