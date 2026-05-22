"""
Parses research_input/italian/raw_research.md (the Deep Research markdown
output) into structured JSON and writes scripts/data/italian/restaurants.json.

The markdown format is loose: numbered entries separated by em-dashes, grouped
under borough headers (### MANHATTAN (N)) and neighborhood subheaders
(**Neighborhood**). This parser extracts:
  - name, address, neighborhood (borough + sub-hood), subtype hint, famous-for,
    format, price_level, typical_dinner_pp, vintage, reservation, michelin, vibe
and emits records compatible with the rest of the pipeline.

Run: python scripts/import_italian_research.py
"""
import re, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from shared import paths

CUISINE = "italian"
SRC = paths.research_dir(CUISINE) / "raw_research.md"
OUT_DISCOVERY = paths.research_dir(CUISINE) / "discovery.json"
OUT_RESTAURANTS = paths.restaurants_json(CUISINE)

# Em-dash variants we may see in copy-pasted output
DASH_RE = re.compile(r"\s*[—–—–]\s*|\s+â\s+|\s+â€“\s+")

PRICE_LEVEL_TO_MIN = {"$": 18, "$$": 40, "$$$": 75, "$$$$": 130}


def detect_borough(line):
    m = re.match(r"^###\s+(MANHATTAN|BROOKLYN|QUEENS|BRONX)", line, re.IGNORECASE)
    return m.group(1).capitalize() if m else None


def detect_neighborhood(line):
    # **West Village / Greenwich Village**
    m = re.match(r"^\*\*([^\*]+)\*\*\s*$", line.strip())
    return m.group(1).strip() if m else None


def detect_entry(line):
    # 1. Name — fields ...
    m = re.match(r"^\s*(\d+)\.\s+(.+)$", line)
    if not m:
        return None
    return m.group(2).strip()


def split_fields(entry_text):
    return [f.strip() for f in DASH_RE.split(entry_text) if f.strip()]


def extract_price_level(text):
    # Find $, $$, $$$, $$$$ in the text (longest match wins)
    m = re.search(r"\$+", text)
    return m.group(0) if m else None


def extract_typical_pp(text):
    # ($70 pp) or ($110)
    m = re.search(r"\(\s*\$?(\d{2,4})\s*(?:pp)?\)", text)
    return int(m.group(1)) if m else None


def extract_year(text):
    m = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", text)
    return int(m.group(1)) if m else None


def classify_subtype(text):
    t = text.lower()
    # Order matters — more specific first
    if "avpn" in t and "neapolitan" in t:
        return "pizzeria-neapolitan-avpn-certified"
    if "pizzeria-neapolitan" in t or "pizzeria neapolitan" in t or ("neapolitan" in t and "pizz" in t):
        return "pizzeria-neapolitan"
    if "pizzeria-nyc" in t or "nyc slice" in t or "nyc-slice" in t:
        return "pizzeria-nyc-slice"
    if "pizzeria-sicilian" in t or "sicilian pizz" in t:
        return "pizzeria-sicilian"
    if "coal-oven" in t or "coal oven" in t:
        return "pizzeria-nyc-slice"
    if "pizzeria-roman" in t or "roman pizz" in t:
        return "pizzeria-roman"
    if "pizzeria" in t:
        return "pizzeria-neapolitan"
    if "red-sauce" in t or "red sauce" in t or "italian-american" in t:
        return "red-sauce"
    if "fine-dining" in t or "fine dining" in t:
        return "fine-dining"
    if "tuscan" in t:
        return "tuscan"
    if "sicilian" in t:
        return "sicilian"
    if "roman" in t:
        return "roman"
    if "northern" in t or "veneto" in t or "emilia" in t or "venetian" in t:
        return "northern"
    if "coastal" in t or "seafood" in t or "clam" in t or "riviera" in t:
        return "southern-coastal"
    if "enoteca" in t or "wine-bar" in t or "wine bar" in t or "vinosteria" in t:
        return "enoteca"
    if "pasta-bar" in t or "pasta bar" in t or "pastificio" in t:
        return "pasta-bar"
    if "modern" in t or "creative" in t:
        return "modern-creative"
    if "osteria" in t:
        return "osteria"
    if "ristorante" in t:
        return "ristorante"
    if "trattoria" in t:
        return "trattoria"
    return "ristorante"


def classify_format(text, subtype):
    t = text.lower()
    if "tasting menu" in t or "pasta tasting" in t:
        return "tasting-menu"
    if "wine-bar" in t or "wine bar" in t or "enoteca" in t:
        return "wine-bar"
    if "pizzeria" in subtype:
        return "pizzeria-quick"
    if "counter" in t:
        return "counter"
    if "fine-dining" in subtype or "ristorante" in subtype or "white-tablecloth" in t:
        return "white-tablecloth"
    return "trattoria-tables"


def classify_vintage(text):
    t = text.lower()
    year = extract_year(text)
    if year:
        # Year of opening mentioned
        age = 2026 - year
        if age >= 20:
            return "institution"
        if age >= 5:
            return "established"
        if age >= 1:
            return "recent"
        return "new"
    if "institution" in t:
        return "institution"
    if "new 2024" in t or "new 2025" in t or "new 2026" in t or "opened 2024" in t or "opened 2025" in t or "opened 2026" in t or " (new)" in t:
        return "new"
    if "recent" in t:
        return "recent"
    if "established" in t:
        return "established"
    return "unknown"


def classify_reservation(text):
    t = text.lower()
    if "hard-to-book" in t or "hard to book" in t or "membership" in t:
        return "hard-to-book"
    if "walk-in" in t and "reservation" in t:
        return "both"
    if "walk-in" in t or "no reservations" in t:
        return "walk-in"
    if "reservation" in t:
        return "reservations"
    return "unknown"


def classify_michelin(text):
    t = text.lower()
    if "michelin 3-star" in t or "3 michelin star" in t or "3-michelin" in t:
        return "3-star"
    if "michelin 2-star" in t or "2 michelin star" in t:
        return "2-star"
    if "michelin 1-star" in t or "1 michelin star" in t or "1-star" in t and "michelin" in t:
        return "1-star"
    if "michelin bib" in t or "bib gourmand" in t:
        return "bib-gourmand"
    if "michelin recommended" in t or "michelin guide" in t:
        return "recommended"
    return "none"


def classify_pasta(text):
    t = text.lower()
    if "pasta-bar" in t or "pastificio" in t or "pasta tasting" in t or "handmade pasta" in t:
        return "extensive-house-made"
    if "fresh pasta" in t or "house pasta" in t or "homemade pasta" in t or "hand-cut pasta" in t:
        return "handmade"
    if "pasta" in t:
        return "basic"
    return "none"


def classify_pizza(text, subtype):
    t = text.lower()
    if "avpn" in t:
        return "neapolitan-avpn-certified"
    if "neapolitan" in t and "pizz" in t:
        return "neapolitan"
    if "coal-oven" in t or "coal oven" in t:
        return "nyc-slice"
    if "sicilian" in t and "pizz" in t:
        return "sicilian"
    if "roman" in t and "pizz" in t:
        return "roman"
    if "pizzeria" in subtype or "wood-fired" in t or "wood fired" in t or "brick-oven" in t or "brick oven" in t:
        return "neapolitan"
    if "pizza" in t:
        return "nyc-slice"
    return "none"


def parse_entry(text, borough, neighborhood):
    fields = split_fields(text)
    if not fields:
        return None
    # Filter out exclusions/skips
    full = text.lower()
    if any(skip in full for skip in [" exclude.", " skip.", " — exclude ", "— exclude.", "(closed", "verify open"]):
        # Check for closed/exclude markers but don't drop "flagged (verify open)" entries
        if "exclude" in full or "skip" in full or full.startswith("closed"):
            return None

    name = fields[0]
    # Address heuristic: looks like a NYC street address
    address = None
    rest_fields = fields[1:]
    if rest_fields and re.search(r"\d", rest_fields[0]) and ("St" in rest_fields[0] or "Ave" in rest_fields[0] or "Blvd" in rest_fields[0] or "Plaza" in rest_fields[0] or "Pl" in rest_fields[0] or "Pkwy" in rest_fields[0] or "Rd" in rest_fields[0]):
        address = rest_fields[0]

    price_level = extract_price_level(text) or "$$"
    typical_pp = extract_typical_pp(text) or PRICE_LEVEL_TO_MIN.get(price_level, 40)
    subtype = classify_subtype(text)
    fmt = classify_format(text, subtype)
    vintage = classify_vintage(text)
    reservation = classify_reservation(text)
    michelin = classify_michelin(text)
    pasta = classify_pasta(text)
    pizza = classify_pizza(text, subtype)

    # famous_for: try to grab the field after subtype hint (typically 2nd-4th field)
    famous_for = ""
    for f in rest_fields:
        # Skip address-looking field
        if f == address:
            continue
        # Skip very short subtype-only fields
        if len(f) < 6:
            continue
        # Skip clearly meta fields (price, reservation, michelin)
        if re.match(r"^\$+", f) or "michelin" in f.lower() or "reservation" in f.lower() or "walk-in" in f.lower() or "hard-to-book" in f.lower():
            continue
        # Looks like a famous-for description (commas, longer)
        if "," in f or len(f) > 20:
            famous_for = f
            break

    # vibe is just the full descriptive text (entry minus name)
    vibe = " — ".join(rest_fields[:6])
    if len(vibe) > 240:
        vibe = vibe[:237] + "..."

    return {
        "name": name,
        "neighborhood": f"{borough} ({neighborhood})" if neighborhood else borough,
        "address": address,
        "price_str": price_level,
        "min_price": typical_pp,
        "pacing": "varies (a la carte)",
        "vibe": vibe,
        "format": subtype,
        "subtype": subtype,
        "famous_for": famous_for,
        "tasting_format": fmt,
        "price_level": price_level,
        "typical_dinner_pp": typical_pp,
        "pasta_program": pasta,
        "pizza_program": pizza,
        "vintage": vintage,
        "reservation": reservation,
        "michelin": michelin,
        "confidence": "high",
    }


def main():
    text = SRC.read_text(encoding="utf-8")
    borough = None
    neighborhood = None
    records = []
    seen = set()

    for line in text.splitlines():
        b = detect_borough(line)
        if b:
            borough = b
            neighborhood = None
            continue
        if not borough:
            continue
        n = detect_neighborhood(line)
        if n:
            neighborhood = n
            continue
        entry_text = detect_entry(line)
        if entry_text:
            rec = parse_entry(entry_text, borough, neighborhood)
            if rec and rec["name"] not in seen:
                records.append(rec)
                seen.add(rec["name"])

    OUT_DISCOVERY.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_RESTAURANTS.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

    counts = {}
    for r in records:
        b = r["neighborhood"].split(" (")[0]
        counts[b] = counts.get(b, 0) + 1

    print(f"Parsed {len(records)} restaurants:")
    for b, c in sorted(counts.items()):
        print(f"  {b}: {c}")
    print(f"Wrote {OUT_DISCOVERY}")
    print(f"Wrote {OUT_RESTAURANTS}")


if __name__ == "__main__":
    main()
