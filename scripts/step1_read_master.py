"""
Step 1: Read the master Excel for a given cuisine and extract restaurant data.

Usage: python scripts/step1_read_master.py [--cuisine omakase]
"""

import pandas as pd
import json
import re
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from config import EXCLUDE_KEYWORDS, MAX_PRICE
from shared import paths

CUISINE = paths.parse_cuisine_arg()
INPUT_PATH = paths.master_xlsx(CUISINE)
OUTPUT_PATH = paths.restaurants_json(CUISINE)


def parse_min_price(price_str):
    if pd.isna(price_str):
        return None
    s = str(price_str).replace("$", "").replace(",", "").replace("~", "").replace("<", "").strip()
    nums = re.findall(r"\d+", s)
    return int(nums[0]) if nums else None


def is_excluded(vibe, price_str):
    combined = f"{vibe} {price_str}".lower()
    return any(kw in combined for kw in EXCLUDE_KEYWORDS)


def main():
    print(f"Reading {INPUT_PATH}...")

    existing = []
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    existing_by_name = {r["name"]: r for r in existing}

    try:
        df = pd.read_excel(INPUT_PATH)
        print(f"Found {len(df)} restaurants in master file.")
    except Exception as e:
        if existing:
            print(f"Could not read Excel ({e.__class__.__name__}). Using cached restaurants.json.")
            print("Tip: close the file in Excel and re-run to pick up any changes.")
            return
        raise RuntimeError(f"Cannot read {INPUT_PATH} and no cached restaurants.json exists.") from e

    excel_records = []
    skipped = 0
    excel_names = set()

    for _, row in df.iterrows():
        name = row["Restaurant Name"]
        hood = row.get("Borough / Neighborhood", "")
        price_str = str(row.get("Price Tiers ($)", ""))
        pacing = str(row.get("Pacing (Mins)", "")) if pd.notna(row.get("Pacing (Mins)")) else ""
        vibe = str(row.get("Vibe & Distinctions", "")) if pd.notna(row.get("Vibe & Distinctions")) else ""
        parkchester = str(row.get("Est. Commute (Parkchester)", ""))
        parkslope = str(row.get("Est. Commute (Park Slope)", ""))
        timediff = str(row.get("Time Diff", ""))

        min_price = parse_min_price(price_str)

        if is_excluded(vibe, price_str):
            skipped += 1
            continue

        excel_names.add(name)
        excel_records.append({
            "name": name,
            "neighborhood": hood if pd.notna(hood) else "",
            "price_str": price_str,
            "min_price": min_price,
            "pacing": pacing,
            "vibe": vibe,
            "commute_parkchester": parkchester,
            "commute_parkslope": parkslope,
            "time_diff": timediff,
        })

    # Preserve records that exist in restaurants.json but not in Excel
    # (e.g. candidates added by add_new_candidates.py from research)
    extras = [r for r in existing if r["name"] not in excel_names]

    restaurants = excel_records + extras

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(restaurants, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(restaurants)} restaurants "
          f"({len(excel_records)} from Excel, {len(extras)} preserved extras, {skipped} excluded).")
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
