"""
Adds the 37 omakase-qualifying new candidates to scripts/restaurants.json.
Parses price ranges from research_input/new_candidates_omakase.json and builds
records matching the existing schema (name, neighborhood, price_str, min_price,
pacing, vibe).

Run once from the repo root: python scripts/add_new_candidates.py
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).parent.parent

candidates = json.loads((ROOT / "research_input" / "new_candidates_omakase.json").read_text(encoding="utf-8"))

# Full price/vibe info pulled from the original 60-entry research doc
PRICE_VIBE = {
    "Warabi Omakase": (108, "$108 14-course AYCE/AYCD over 80min (LIC value omakase)"),
    "Sushi Hayashi (Williamsburg)": (98, "$98/80min, 14-course omakase + 2 AYCE refill rounds (Williamsburg)"),
    "Toka Chef Kitchen": (58, "$58-$98, 14-18 course omakase + AYCE nigiri (from Matsunori team)"),
    "Sushi Sho": (450, "3-Michelin Edomae from Tokyo legend Keiji Nakazawa, Andaz 5th Ave"),
    "Muku": (295, "Tribeca kaiseki, 1 Michelin star in 2 months (Kuma Hospitality)"),
    "Yamada": (300, "10-seat hinoki counter kaiseki from Isao Yamada (ex-Brushstroke)"),
    "Odo East Village": (150, "Kaiseki-izakaya from 2-Michelin Hiroki Odo, late-night"),
    "Yoshoku": (188, "Waldorf Astoria lobby kaiseki tasting; chef ex-Zero Bond"),
    "Yūgin": (400, "Hidden in private club 37th floor; chef ex-Masa; 72 micro-seasons"),
    "Anbā": (220, "16-course kaiseki, female chef Ambrely Ouimette, dry-age fish program"),
    "Enso Omakase": (195, "16-course chef Nick Wang (Ako/Amami); Eater Restaurants to Watch"),
    "Hear & There": (105, "Behind sliding door in Williamsburg listening lounge, 22-seat counter"),
    "Kansha": (145, "Carnegie Hill Nikkei (Japanese-Peruvian) from Sushi Noz alum"),
    "Ikigai": (165, "12-seat subterranean kaiseki, all proceeds donated"),
    "Sushi Ichimura": (425, "Eiji Ichimura's 20-course Edomae, signature uni+caviar monaka"),
    "Sushi Ishikawa": (135, "Truffle/caviar/gold-leaf/foie gras stacking, 17-course MATSU"),
    "Nakaji": (365, "10-seat Edomae with comparative uni tasting from Toyosu auction"),
    "Shion 69 Leonard Street": (480, "Edomae with rare Edo-period chinmi (CAVEAT: closed early 2026)"),
    "Shuko": (270, "Cult counter from Nick Kim/Jimmy Lau (ex-Masa); secret toro/uni/caviar toast"),
    "Kurumazushi": (300, "Original toro-flight specialist (since 1977), 16-course omakase"),
    "icca": (400, "8-seat counter with rare Edo chinmi + Italo-Japanese capellini bridge"),
    "Masa": (950, "Only 3-Michelin Japanese in America; no Ã  la carte, no photos"),
    "Bar Masa": (290, "Masa-family Ã  la carte + sushi tasting; toro tartare with caviar"),
    "Kappo Masa": (300, "Masa-family hybrid counter+tables UES; sukiyaki, caviar/truffle dishes"),
    "Togyushi": (200, "Wagyu kappo+omakase counter with exclusive G1 Zao Wagyu (Yamagata)"),
    "Omi Omakase": (109, "Flushing Edomae counter, $159 tier has A5 wagyu + Hokkaido uni"),
    "Himitsu Flushing": (150, "First speakeasy-style omakase in Queens, hidden inside Siam Thai"),
    "Kakurega Sushi": (145, "Flushing 7-seat counter, A5 wagyu nigiri add-on, fish flown from Japan"),
    "Kaizen (Wabi Nori Hand Roll Bar)": (55, "Hand-roll + omakase + izakaya hybrid in Flushing"),
    "That Place Omakase": (98, "Less-publicized Flushing omakase, wagyu in upper tier"),
    "Kaiyo Omakase": (130, "Reasonably-priced LIC counter omakase, 15- and 18-course tiers"),
    "Omakase Osukāā LIC": (180, "LIC counter omakase; seasonal Japanese fish, wagyu in higher courses"),
    "Honzen Japanese Eatery": (35, "Astoria honzen-ryori prix fixe with A5 wagyu + uni don options"),
    "Sapps": (30, "LIC izakaya with $30 8-piece sushi omakase set + yakitori"),
    "Hibino LIC": (48, "LIC izakaya with $48 omakase (+$15 uni upgrade), housemade tofu"),
    "Bushniwa": (60, "Bushwick brasserie with reservation-only full omakase, niche"),
    "Nigiri (by Honshu)": (140, "Jersey City counter omakase hidden behind Honshu Lounge"),
}

# Normalize neighborhood text to match dataset style: "Borough (Hood)"
def normalize_hood(nh):
    nh = nh.replace("—", " - ")  # em dash to hyphen
    # "Queens - Flushing" -> "Queens (Flushing)"
    m = re.match(r"^([A-Za-z\s]+?)\s*-\s*(.+?)$", nh)
    if m:
        borough = m.group(1).strip()
        hood = m.group(2).strip()
        return f"{borough} ({hood})"
    return nh

new_records = []
for c in candidates:
    name = c["name"]
    if name not in PRICE_VIBE:
        print(f"WARN: no price/vibe for {name}")
        price, vibe = 100, c.get("tasting_format", "")
    else:
        price, vibe = PRICE_VIBE[name]
    new_records.append({
        "name": name,
        "neighborhood": normalize_hood(c["neighborhood"]),
        "price_str": str(price),
        "min_price": price,
        "pacing": "60-90",
        "vibe": vibe,
    })

# Merge into restaurants.json (skip names already present)
restaurants_path = ROOT / "scripts" / "restaurants.json"
existing = json.loads(restaurants_path.read_text(encoding="utf-8"))
existing_names = {r["name"] for r in existing}
added = 0
for r in new_records:
    if r["name"] not in existing_names:
        existing.append(r)
        added += 1
restaurants_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Added {added} new records. Total: {len(existing)}")
