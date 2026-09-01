---
description: Rebuild all cuisine outputs and verify nothing broke
---

Rebuild the pipeline outputs and verify:

1. Run `python scripts/run.py --all` from the repo root.
2. Expected: each cuisine prints read/scored/wrote lines. The ONLY acceptable warning is the known omakase collision report (3 groups / 6 restaurants). Any NEW collision group or traceback is a regression — stop and report it, do not fix silently.
3. Run `python -m pytest tests/ -q`. Expected: 142 passed, 4 skipped (more passed is fine if tests were added).
4. `git diff --stat` — the 4 root `*.xlsx` files always churn (timestamp bytes, expected). Anything else changed must be explainable by the task at hand.
5. Report the results in 3 lines.
