"""CLI: run the pipeline for one or all cuisines.

Usage:
  python scripts/run.py --cuisine omakase
  python scripts/run.py --cuisine italian --steps score,output
  python scripts/run.py --all
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import pipeline
from scripts.cuisines import _REGISTRY, get_cuisine


ALL_STEPS = ("score", "output")


def run(cuisine_name: str, steps: list[str]) -> None:
    print(f"=== {cuisine_name} ===")
    cuisine = get_cuisine(cuisine_name)
    restaurants = pipeline.read(cuisine)
    print(f"  read: {len(restaurants)} restaurants")

    scored: dict = {}
    if "score" in steps:
        scored = pipeline.score_step(cuisine, restaurants)
        print(f"  scored: {len(scored)} restaurants")

    if "output" in steps:
        user_state = pipeline.load_user_state(cuisine)
        enriched = pipeline.enrich(cuisine, restaurants, scored, user_state)
        scored_path = pipeline.write_scored_json(cuisine, enriched)
        dash_path = pipeline.write_dashboard_data(cuisine, enriched)
        xlsx_path = pipeline.write_excel(cuisine, enriched)
        print(f"  wrote: {scored_path}")
        print(f"  wrote: {dash_path}")
        print(f"  wrote: {xlsx_path}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--cuisine", default="omakase", help="cuisine name (default: omakase)")
    p.add_argument("--all", action="store_true", help="run all registered cuisines")
    p.add_argument("--steps", default=",".join(ALL_STEPS),
                   help=f"comma-separated subset of {ALL_STEPS} (default: all)")
    args = p.parse_args(argv)

    steps = [s.strip() for s in args.steps.split(",") if s.strip()]
    unknown = [s for s in steps if s not in ALL_STEPS]
    if unknown:
        p.error(f"unknown steps: {unknown}. valid: {ALL_STEPS}")

    cuisines = list(_REGISTRY) if args.all else [args.cuisine]
    for c in cuisines:
        run(c, steps)
    return 0


if __name__ == "__main__":
    sys.exit(main())
