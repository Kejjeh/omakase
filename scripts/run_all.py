"""
Run the full restaurant analysis pipeline for one cuisine (or all).

Usage:
  python scripts/run_all.py                       # runs omakase (default)
  python scripts/run_all.py --cuisine italian     # runs italian
  python scripts/run_all.py --all                 # runs every cuisine in paths.CUISINES
  python scripts/run_all.py --refresh             # clears the cuisine's ratings cache first

Steps (per cuisine):
  1. Read master Excel -> restaurants.json
  2. Fetch Google ratings -> ratings_cache.json
  2b. Fetch Infatuation ratings -> infatuation_cache.json
  3. Compute Wilson-adjusted scores + merge specialty data -> scored_restaurants.json
  4. Generate output Excel -> <Cuisine>_Ratings.xlsx
  5. Rebuild docs/<cuisine>/index.html ALL_DATA block
"""

import subprocess
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared import paths

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    ("Step 1:  Reading master spreadsheet",       "step1_read_master.py"),
    ("Step 2:  Fetching Google ratings",          "step2_fetch_ratings.py"),
    ("Step 2b: Fetching Infatuation ratings",     "step2b_fetch_infatuation.py"),
    ("Step 3:  Computing value scores",           "step3_compute_scores.py"),
    ("Step 4:  Generating output spreadsheet",    "step4_generate_output.py"),
    ("Step 5:  Rebuilding dashboard ALL_DATA",    "rebuild_html_data.py"),
]


def run_for_cuisine(cuisine, refresh):
    if refresh:
        cache = paths.ratings_cache(cuisine)
        if cache.exists():
            cache.unlink()
            print(f"  Cleared {cache}")

    print("=" * 60)
    print(f"  PIPELINE: {cuisine}")
    print("=" * 60)
    start = time.time()
    for label, script in STEPS:
        print(f"\n{'─' * 60}\n  {label}\n{'─' * 60}")
        script_path = os.path.join(SCRIPTS_DIR, script)
        env = os.environ.copy()
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PYTHONIOENCODING", "utf-8")
        result = subprocess.run(
            [sys.executable, script_path, "--cuisine", cuisine],
            cwd=os.path.dirname(SCRIPTS_DIR),
            env=env,
        )
        if result.returncode != 0:
            print(f"\n  FAILED at {script} (exit code {result.returncode})")
            sys.exit(1)
    print(f"\n  [{cuisine}] COMPLETE ({time.time() - start:.1f}s)\n")


def main():
    argv = sys.argv[:]
    refresh = "--refresh" in argv
    if refresh:
        argv.remove("--refresh")
    run_all = "--all" in argv
    if run_all:
        argv.remove("--all")

    if run_all:
        cuisines = paths.CUISINES
    else:
        sys.argv = argv  # so parse_cuisine_arg picks up --cuisine
        cuisines = [paths.parse_cuisine_arg()]

    for cuisine in cuisines:
        run_for_cuisine(cuisine, refresh)


if __name__ == "__main__":
    main()
