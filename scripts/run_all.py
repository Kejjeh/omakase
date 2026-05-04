"""
Run the full Omakase analysis pipeline.

Usage:
  python scripts/run_all.py             # Run all steps
  python scripts/run_all.py --refresh   # Clear ratings cache and re-fetch from Google

Steps:
  1. Read master Excel -> restaurants.json
  2. Fetch Google ratings -> ratings_cache.json (cached, only fetches new restaurants)
  3. Compute Bayesian-adjusted scores -> scored_restaurants.json
  4. Generate output Excel -> Omakase_Ratings.xlsx
"""

import subprocess
import sys
import os
import time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    ("Step 1: Reading master spreadsheet", "step1_read_master.py"),
    ("Step 2: Fetching Google ratings", "step2_fetch_ratings.py"),
    ("Step 3: Computing value scores", "step3_compute_scores.py"),
    ("Step 4: Generating output spreadsheet", "step4_generate_output.py"),
]


def main():
    if "--refresh" in sys.argv:
        cache_path = os.path.join(SCRIPTS_DIR, "ratings_cache.json")
        if os.path.exists(cache_path):
            os.remove(cache_path)
            print("Cleared ratings cache. Will re-fetch all from Google.\n")

    print("=" * 60)
    print("  OMAKASE ANALYSIS PIPELINE")
    print("=" * 60)

    start = time.time()
    for label, script in STEPS:
        print(f"\n{'─' * 60}")
        print(f"  {label}")
        print(f"{'─' * 60}")
        script_path = os.path.join(SCRIPTS_DIR, script)
        result = subprocess.run([sys.executable, script_path], cwd=os.path.dirname(SCRIPTS_DIR))
        if result.returncode != 0:
            print(f"\n  FAILED at {script} (exit code {result.returncode})")
            sys.exit(1)

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"  PIPELINE COMPLETE ({elapsed:.1f}s)")
    print(f"  Output: Omakase_Ratings.xlsx")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
