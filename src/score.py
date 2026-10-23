"""
score.py: score and rank sample distributors as Ultrachem leads.

IMPORTANT: This scoring is rules-based. It is NOT an AI model.
The weights, categories, and disqualifiers below are our team's assumptions.
They follow the scope from the client call, but they are not validated.
Several are pending the on-site visit and are marked that way.

The "why commercially attractive" and "recommended next step" text is built
from fixed templates, not written by AI.

Input:  data/sample_companies.csv
Output: data/scored_leads.csv (ranked, with reasons, status, and next steps)

Run from the repo root:
    .venv\\Scripts\\python.exe src/score.py
"""

from pathlib import Path

import pandas as pd


# =====================================================================
# SCORING SETTINGS: edit this block after the on-site visit
# All values are assumptions until Ultrachem's sales team confirms them.
# =====================================================================

# Target region, confirmed at the on-site visit.
TARGET_STATES = ["GA", "NC", "SC", "VA"]
TARGET_REGION_NAME = "Georgia, North Carolina, South Carolina, and Virginia"

# Points for each part of the score. They add up to 100.
WEIGHTS = {
    "product_fit": 45,  # sells the product lines Ultrachem makes and is in scope
    "size_fit": 20,     # ASSUMPTION pending on-site visit: more locations = more volume
    "brand_fit": 20,    # ASSUMPTION pending on-site visit: already sells other fluid brands
    "type_fit": 15,     # what kind of distributor it is
}

# Product lines in scope from the client call. These earn product points.
ULTRACHEM_CATEGORIES = [
    # Transportation
    "motorcycle oil",
    "passenger vehicle oil",
    "commercial vehicle oil",
    "marine oil",
    "power generation oil",   # UNCONFIRMED: our reading of "electrical power"
    "locomotive oil",
    "transmission oil",
    "gear oil",
    # Water-based
    "coolant",
    "antifreeze",
    "refrigeration fluid",
]

# Older Ultrachem lines not named in the new scope. Zero weight.
# Unconfirmed, ask sales whether these should count.
UNCONFIRMED_CATEGORIES = [
    "hydraulic fluid",
    "rust protective oil",
    "heat transfer fluid",
    "agricultural spray oil",
]

# The client said no aviation fluids. These never count as a match.
EXCLUDED_CATEGORIES = ["aviation fluid"]

# A company that matches this many in-scope lines gets full product points.
MATCHES_FOR_FULL_PRODUCT_POINTS = 4

# Size from number of locations. ASSUMPTION pending on-site visit.
# Each row is (minimum locations, share of size points, label).
SIZE_BANDS = [
    (6, 1.0, "large"),
    (3, 0.7, "medium"),
    (1, 0.4, "small"),
]

# Brand signal: other fluid brands the distributor already carries.
# ASSUMPTION pending on-site visit: carrying brands means it has buyers for fluids.
BRANDS_FOR_FULL_BRAND_POINTS = 2

# Share of the type points each distributor type earns (0 to 1).
# A type not listed here earns 0.
TYPE_FIT = {
    "auto parts": 1.0,
    "truck and fleet parts": 1.0,
    "marine supply": 1.0,
    "powersports": 0.9,
    "power equipment": 0.8,
    "HVAC and refrigeration supply": 0.8,
    "rail supply": 0.7,
}

# Disqualifiers. Any one of these removes a lead from the recommended list.
# Delete or comment out a line to turn that rule off.
DISQUALIFIERS = {
    "aviation_only": "Sells aviation fluids only. Ultrachem does not sell aviation fluids.",
    "outside_target_region": f"Located outside the target region: {TARGET_REGION_NAME}.",
    "not_a_distributor": "Not a distributor. Only distributors are in scope right now.",
    # From the on-site visit: a distributor has a warehouse that receives truckloads and its own sales team.
    "no_distributor_infrastructure": "Has no warehouse or no sales team of its own, so it does not qualify as a distributor.",
    # ASSUMPTION, ours and not the company's rule: existing customers go to account managers, not new outreach.
    "existing_customer": "Already carries Ultrachem, so it is an existing customer, not a new lead.",
    "no_product_match": "Sells none of the Ultrachem product lines in scope.",
}

# Recommended next step. Score thresholds are assumptions.
CALL_THRESHOLD = 70   # high confidence and at least this score: call
EMAIL_THRESHOLD = 45  # at least this score: email
NEXT_STEPS = {
    "disqualified": "Do not pursue. {reason}",
    "needs_review": "Verify the record before contacting. Find the missing {missing}, then re-score.",
    "call": "Call the purchasing contact this week. Offer samples of {lines}.",
    "email": "Send an intro email with the {lines} catalog. Follow up in one week.",
    "low": "Low priority. Revisit after the higher-ranked leads.",
}

# Fields we check for confidence. Each blank one lowers confidence.
# "none" in fluid_brands_carried means the company carries no brands. Blank means unknown.
KEY_FIELDS = [
    "business_type", "distributor_type", "city", "state", "website",
    "locations", "product_lines", "fluid_brands_carried", "aviation_only",
    "has_warehouse", "has_sales_team",
]

# =====================================================================
# END OF SCORING SETTINGS
# =====================================================================


REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = REPO_ROOT / "data" / "sample_companies.csv"
OUTPUT_FILE = REPO_ROOT / "data" / "scored_leads.csv"

FIELD_LABELS = {
    "business_type": "business type",
    "distributor_type": "distributor type",
    "fluid_brands_carried": "brands carried",
    "product_lines": "product lines",
    "aviation_only": "aviation status",
    "has_warehouse": "warehouse status",
    "has_sales_team": "sales team status",
}


def split_list(text):
    """Turn 'gear oil; coolant' into ['gear oil', 'coolant']."""
    return [item.strip() for item in str(text).split(";") if item.strip()]


def plain_list(items):
    """Turn ['a', 'b', 'c'] into 'a, b, and c'."""
    if len(items) <= 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + ", and " + items[-1]


def find_missing(row):
    """Return the key fields that are blank for this company."""
    return [field for field in KEY_FIELDS if str(row[field]).strip() == ""]


def get_points(weight, share):
    """Turn a weight and a share (0 to 1) into whole points, rounding .5 up."""
    return int(weight * share + 0.5)


def get_size_band(locations):
    """Return (share, label) for a number of locations, or (0, None) if unknown."""
    if str(locations).strip() == "":
        return 0.0, None
    count = int(float(locations))
    for minimum, share, label in SIZE_BANDS:
        if count >= minimum:
            return share, label
    return 0.0, None


def count_locations(locations):
    """Turn 1 into '1 location' and 3 into '3 locations'."""
    count = int(float(locations))
    return f"{count} location" if count == 1 else f"{count} locations"


def get_brands(row):
    """Return the other fluid brands carried, without Ultrachem."""
    brands = [b for b in split_list(row["fluid_brands_carried"]) if b.lower() != "none"]
    return [b for b in brands if b.lower() != "ultrachem"]


def get_confidence(row):
    """
    Return a confidence level and the notes that explain it.
    Uses only data_completeness and blank key fields.
    Levels: "high", "medium", or "needs review".
    """
    notes = []
    missing = find_missing(row)
    completeness = row["data_completeness"] or "unknown"

    if missing:
        notes.append("Missing: " + ", ".join(missing) + ".")
    notes.append(f"Data completeness is {completeness}.")

    if completeness == "low" or completeness == "unknown" or len(missing) >= 2:
        level = "needs review"
        notes.append("Too little data to trust this score. A person should check it.")
    elif completeness == "medium" or len(missing) == 1:
        level = "medium"
    else:
        level = "high"

    return level, notes


def check_disqualifiers(row, listed, matches):
    """
    Return the names of the disqualifiers that apply.
    A blank field never disqualifies. Unknown data goes to review instead.
    """
    hits = []
    if row["aviation_only"] == "yes":
        hits.append("aviation_only")
    if row["state"] and row["state"] not in TARGET_STATES:
        hits.append("outside_target_region")
    if row["business_type"] and row["business_type"] != "distributor":
        hits.append("not_a_distributor")
    if row["has_warehouse"] == "no" or row["has_sales_team"] == "no":
        hits.append("no_distributor_infrastructure")
    if "ultrachem" in [b.lower() for b in split_list(row["fluid_brands_carried"])]:
        hits.append("existing_customer")
    if listed and not matches:
        hits.append("no_product_match")
    # Only keep rules that are still turned on in the settings block.
    return [name for name in hits if name in DISQUALIFIERS]


def write_why_attractive(row, matches, size_label, brands):
    """One or two template sentences on why this lead is worth pursuing."""
    where = f" in {row['city']}" if row["city"] else ""
    kind = row["distributor_type"] or "distributor"
    first = f"{kind[0].upper() + kind[1:]} distributor{where}"
    if size_label:
        first += f" with {count_locations(row['locations'])} ({size_label})"
    first += "."
    count = len(matches)
    lines_word = "line" if count == 1 else "lines"
    second = f"Sells {count} Ultrachem product {lines_word} in scope: {plain_list(matches)}."
    if brands:
        brand_word = "brand" if len(brands) == 1 else "brands"
        second += f" Already carries {len(brands)} other fluid {brand_word}, so it has buyers for these products."
    return first + " " + second


def write_next_step(status, score, confidence, matches, missing, disqualifiers):
    """Pick a recommended next step from the NEXT_STEPS templates."""
    if status == "disqualified":
        return NEXT_STEPS["disqualified"].format(reason=DISQUALIFIERS[disqualifiers[0]])
    if status == "needs review":
        fields = [FIELD_LABELS.get(f, f) for f in missing] or ["details"]
        return NEXT_STEPS["needs_review"].format(missing=plain_list(fields))
    lines = plain_list(matches[:2])
    if score >= CALL_THRESHOLD and confidence == "high":
        return NEXT_STEPS["call"].format(lines=lines)
    if score >= EMAIL_THRESHOLD:
        return NEXT_STEPS["email"].format(lines=lines)
    return NEXT_STEPS["low"]


def score_company(row):
    """
    Score one company from its structured columns only (not notes).
    Returns a dict with the score (0 to 100), reasons, confidence, points for each part,
    matched lines, disqualifiers, status, why_attractive, and recommended_next_step.
    """
    reasons = []
    points_by_part = {}

    # 1. Product fit: how many in-scope lines the company sells.
    listed = split_list(row["product_lines"])
    matches = [c for c in listed if c in ULTRACHEM_CATEGORIES]
    unconfirmed = [c for c in listed if c in UNCONFIRMED_CATEGORIES]
    excluded = [c for c in listed if c in EXCLUDED_CATEGORIES]
    others = [c for c in listed if c not in matches + unconfirmed + excluded]
    share = min(len(matches), MATCHES_FOR_FULL_PRODUCT_POINTS) / MATCHES_FOR_FULL_PRODUCT_POINTS
    points = get_points(WEIGHTS["product_fit"], share)
    points_by_part["product_fit"] = points
    if matches:
        word = "line" if len(matches) == 1 else "lines"
        reasons.append(f"Sells {len(matches)} in-scope Ultrachem {word}: {', '.join(matches)} "
                       f"(+{points} of {WEIGHTS['product_fit']}).")
    elif listed:
        reasons.append(f"Sells products, but none are in-scope Ultrachem lines (+0 of {WEIGHTS['product_fit']}).")
    else:
        reasons.append(f"No product lines on record (+0 of {WEIGHTS['product_fit']}).")
    if unconfirmed:
        reasons.append("Also sells " + ", ".join(unconfirmed) + ". Unconfirmed lines, ask sales (0 points).")
    if excluded:
        reasons.append("Sells " + ", ".join(excluded) + ". Out of scope, no aviation fluids (0 points).")
    if others:
        reasons.append("Also sells products Ultrachem does not make: " + ", ".join(others) + ".")

    # 2. Size fit from number of locations.
    share, size_label = get_size_band(row["locations"])
    points = get_points(WEIGHTS["size_fit"], share)
    points_by_part["size_fit"] = points
    if size_label:
        reasons.append(f"Has {count_locations(row['locations'])}, {size_label} "
                       f"(+{points} of {WEIGHTS['size_fit']}).")
    else:
        reasons.append(f"Number of locations unknown (+0 of {WEIGHTS['size_fit']}).")

    # 3. Brand signal: other fluid brands carried.
    brands = get_brands(row)
    share = min(len(brands), BRANDS_FOR_FULL_BRAND_POINTS) / BRANDS_FOR_FULL_BRAND_POINTS
    points = get_points(WEIGHTS["brand_fit"], share)
    points_by_part["brand_fit"] = points
    if brands:
        reasons.append(f"Carries other fluid brands: {', '.join(brands)} (+{points} of {WEIGHTS['brand_fit']}).")
    elif row["fluid_brands_carried"]:
        reasons.append(f"Carries no other fluid brands (+0 of {WEIGHTS['brand_fit']}).")
    else:
        reasons.append(f"Brands carried unknown (+0 of {WEIGHTS['brand_fit']}).")

    # 4. Distributor type fit.
    kind = row["distributor_type"]
    points = get_points(WEIGHTS["type_fit"], TYPE_FIT.get(kind, 0.0))
    points_by_part["type_fit"] = points
    reasons.append(f"Distributor type is {kind or 'unknown'} (+{points} of {WEIGHTS['type_fit']}).")

    total = sum(points_by_part.values())
    confidence, confidence_notes = get_confidence(row)
    disqualifiers = check_disqualifiers(row, listed, matches)
    missing = find_missing(row)

    # Status: disqualified first, then thin data, then recommended.
    if disqualifiers:
        status = "disqualified"
    elif confidence == "needs review":
        status = "needs review"
    else:
        status = "recommended"

    if status == "disqualified":
        why = ""
    else:
        why = write_why_attractive(row, matches, size_label, brands)

    return {
        "score": total,
        "reasons": reasons,
        "confidence": confidence,
        "confidence_notes": confidence_notes,
        "points": points_by_part,
        "matched": matches,
        "disqualifiers": disqualifiers,
        "status": status,
        "why_attractive": why,
        "recommended_next_step": write_next_step(status, total, confidence, matches, missing, disqualifiers),
    }


def rank_companies(companies):
    """Score every company and return a table sorted from best to worst."""
    companies = companies.fillna("").astype(str)  # treat blank cells as empty text
    companies["locations"] = companies["locations"].str.replace(".0", "", regex=False)
    results = [score_company(row) for _, row in companies.iterrows()]

    ranked = companies.copy()
    ranked["score"] = [r["score"] for r in results]
    ranked["status"] = [r["status"] for r in results]
    ranked["confidence"] = [r["confidence"] for r in results]
    ranked["needs_review"] = ranked["confidence"] == "needs review"
    ranked["why_attractive"] = [r["why_attractive"] for r in results]
    ranked["recommended_next_step"] = [r["recommended_next_step"] for r in results]
    # Join lists with " | " so each cell stays readable in a CSV.
    ranked["reasons"] = [" | ".join(r["reasons"]) for r in results]
    ranked["confidence_notes"] = [" | ".join(r["confidence_notes"]) for r in results]
    ranked["disqualified_by"] = ["; ".join(r["disqualifiers"]) for r in results]
    ranked["disqualify_reasons"] = [" | ".join(DISQUALIFIERS[d] for d in r["disqualifiers"]) for r in results]
    # Point breakdown, so the app can show it without parsing the reasons text.
    for part in WEIGHTS:
        column = part.replace("_fit", "_points")  # product_fit -> product_points
        ranked[column] = [r["points"][part] for r in results]
    ranked["matched_count"] = [len(r["matched"]) for r in results]
    ranked["matched_lines"] = ["; ".join(r["matched"]) for r in results]
    ranked["missing_fields"] = ["; ".join(find_missing(row)) for _, row in companies.iterrows()]
    ranked["score_method"] = "rules-based (not AI), assumed criteria"

    # Disqualified leads go last. Then highest score first.
    # Ties go to more matched lines, then more complete data, then name A to Z.
    completeness_order = {"high": 0, "medium": 1, "low": 2}
    ranked["_disqualified"] = ranked["status"] == "disqualified"
    ranked["_completeness"] = ranked["data_completeness"].map(completeness_order).fillna(3)
    ranked = ranked.sort_values(
        ["_disqualified", "score", "matched_count", "_completeness", "name"],
        ascending=[True, False, False, True, True],
    )
    ranked = ranked.drop(columns=["_disqualified", "_completeness"])
    # Rank counts only leads that are not disqualified. Disqualified leads have no rank.
    eligible = (ranked["status"] != "disqualified").sum()
    ranked.insert(0, "rank", list(range(1, eligible + 1)) + [""] * (len(ranked) - eligible))

    columns = [
        "rank", "name", "score", "status", "confidence", "needs_review",
        "why_attractive", "recommended_next_step", "reasons", "confidence_notes",
        "disqualified_by", "disqualify_reasons",
        "product_points", "size_points", "brand_points", "type_points",
        "matched_count", "matched_lines", "missing_fields",
        "business_type", "distributor_type", "city", "state", "website", "locations",
        "product_lines", "fluid_brands_carried", "aviation_only", "has_warehouse", "has_sales_team",
        "data_completeness", "data_source", "score_method",
    ]
    return ranked[columns]


if __name__ == "__main__":
    companies = pd.read_csv(INPUT_FILE)
    ranked = rank_companies(companies)
    ranked.to_csv(OUTPUT_FILE, index=False)
    print(f"Scored {len(ranked)} companies. Saved to {OUTPUT_FILE}")
    print(ranked[["rank", "name", "score", "status", "confidence"]].to_string(index=False))
