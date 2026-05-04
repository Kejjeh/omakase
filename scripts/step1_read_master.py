"""
Step 1: Read the master Omakase.xlsx and extract restaurant data.
Outputs: scripts/restaurants.json
"""

import pandas as pd
import json
import re
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from config import MASTER_EXCEL, EXCLUDE_KEYWORDS, MAX_PRICE

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(PROJECT_ROOT, MASTER_EXCEL)
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "scripts", "restaurants.json")


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

    try:
        df = pd.read_excel(INPUT_PATH)
        print(f"Found {len(df)} restaurants in master file.")
    except Exception as e:
        if os.path.exists(OUTPUT_PATH):
            print(f"Could not read Excel ({e.__class__.__name__}). Using cached restaurants.json.")
            print("Tip: close the file in Excel and re-run to pick up any changes.")
            return
        else:
            raise RuntimeError(f"Cannot read {INPUT_PATH} and no cached restaurants.json exists.") from e

    restaurants = []
    skipped = 0

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

        restaurants.append({
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

    with open(OUTPUT_PATH, "w") as f:
        json.dump(restaurants, f, indent=2)

    print(f"Exported {len(restaurants)} restaurants ({skipped} excluded).")
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
