---
description: Fast sanity check that the project still works (run after any change)
---

Run the finish checklist from CLAUDE.md:

1. `python -m pytest tests/ -q` → expect `142 passed, 4 skipped` (~0.3s).
2. `python scripts/run.py --all` → completes; only expected warning is the known 3-group omakase collision report.
3. `git diff --stat` → only intended files changed (plus `*.xlsx` timestamp churn, which is normal).

Report pass/fail for each in 3 lines. On any failure, show the failing output verbatim and stop — do not attempt broad fixes without asking.
