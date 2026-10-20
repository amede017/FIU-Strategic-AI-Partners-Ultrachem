"""
score.py: score and rank sample companies as Ultrachem leads.

IMPORTANT: This scoring is rules-based. It is NOT an AI model.
The weights and categories below are our team's assumptions.
They are not validated and will change after the client confirms
the target segment and lead criteria.

Input:  data/sample_companies.csv
Output: data/scored_leads.csv (ranked, with reasons and confidence)

Run from the repo root:
    .venv\\Scripts\\python.exe src/score.py
"""

from pathlib import Path

import pandas as pd


# =====================================================================
# SCORING SETTINGS: edit this block after the client call
# All values are assumptions until the client confirms them.
# =====================================================================

# Points for each part of the score. They add up to 100.
WEIGHTS = {
    "product_fit": 50,  # does the company sell or use what Ultrachem makes?
    "type_fit": 20,     # distributor, private label, OEM, or end user
    "segment_fit": 20,  # which market the company is in
    "region_fit": 10,   # where the company is
}

# Ultrachem product categories, matching the labels in sample_companies.csv.
ULTRACHEM_CATEGORIES = [
    "passenger car oil",
    "commercial vehicle oil",
    "motorcycle oil",
    "marine oil",
    "RV oil",
    "transmission fluid",
    "gear oil",
    "hydraulic fluid",
    "rust protective oil",
    "heat transfer fluid",
    "agricultural spray oil",
]

# A company that matches this many categories gets full product points.
MATCHES_FOR_FULL_PRODUCT_POINTS = 4

# If a company matches no Ultrachem categories, its total score is capped here.
# This keeps a company with a good type or region from ranking high
# when it does not sell anything Ultrachem makes.
NO_PRODUCT_MATCH_CAP = 20

# Share of the type, segment, and region points each value earns (0 to 1).
# A value not listed here earns 0.
TYPE_FIT = {
    "distributor": 1.0,
    "private label": 1.0,
    "OEM": 0.9,
    "end user": 0.6,
}

SEGMENT_FIT = {
    "distributor": 1.0,
    "fleet service": 0.8,
    "industrial maintenance": 0.8,
    "marine and RV": 0.8,
    "agricultural": 0.8,
    "other": 0.0,
}

REGION_FIT = {
    "US Southeast": 1.0,
    "US Midwest": 1.0,
    "US Northeast": 1.0,
    "US Southwest": 1.0,
    "US West": 1.0,
    "Caribbean": 0.7,
    "Latin America": 0.7,
    "Europe": 0.5,
}

# Fields we check for confidence. Each blank one lowers confidence.
KEY_FIELDS = ["type", "segment", "region", "website", "product_categories"]

# =====================================================================
# END OF SCORING SETTINGS
# =====================================================================


REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = REPO_ROOT / "data" / "sample_companies.csv"
OUTPUT_FILE = REPO_ROOT / "data" / "scored_leads.csv"


def split_categories(text):
    """Turn 'gear oil; hydraulic fluid' into ['gear oil', 'hydraulic fluid']."""
    return [item.strip() for item in text.split(";") if item.strip()]


def get_confidence(row):
    """
    Return a confidence level and the notes that explain it.
    Uses only data_completeness and blank key fields.
    Levels: "high", "medium", or "needs review".
    """
    notes = []
    missing = [field for field in KEY_FIELDS if row[field] == ""]
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


def score_company(row):
    """
    Score one company from its structured columns only (not notes).
    Returns a dict with score (0 to 100), reasons, confidence, and confidence notes.
    """
    reasons = []
    total = 0.0

    # 1. Product fit: how many Ultrachem categories the company lists.
    listed = split_categories(row["product_categories"])
    matches = [c for c in listed if c in ULTRACHEM_CATEGORIES]
    others = [c for c in listed if c not in ULTRACHEM_CATEGORIES]
    share = min(len(matches), MATCHES_FOR_FULL_PRODUCT_POINTS) / MATCHES_FOR_FULL_PRODUCT_POINTS
    points = WEIGHTS["product_fit"] * share
    total += points
    if matches:
        word = "category" if len(matches) == 1 else "categories"
        reasons.append(
            f"Matches {len(matches)} Ultrachem product {word}: {', '.join(matches)} "
            f"(+{points:.0f} of {WEIGHTS['product_fit']})."
        )
    else:
        reasons.append(f"No Ultrachem product categories listed (+0 of {WEIGHTS['product_fit']}).")
    if others:
        reasons.append("Also lists categories Ultrachem does not make: " + ", ".join(others) + ".")

    # 2. Type, segment, and region fit use the same lookup pattern.
    lookups = [
        ("type", "type_fit", TYPE_FIT, "Company type"),
        ("segment", "segment_fit", SEGMENT_FIT, "Segment"),
        ("region", "region_fit", REGION_FIT, "Region"),
    ]
    for column, weight_name, table, label in lookups:
        value = row[column]
        points = WEIGHTS[weight_name] * table.get(value, 0.0)
        total += points
        shown = value if value else "unknown"
        reasons.append(f"{label} is {shown} (+{points:.0f} of {WEIGHTS[weight_name]}).")

    # 3. Cap the score when nothing Ultrachem makes is a match.
    if not matches and total > NO_PRODUCT_MATCH_CAP:
        total = NO_PRODUCT_MATCH_CAP
        reasons.append(f"Score capped at {NO_PRODUCT_MATCH_CAP} because no product categories match.")

    confidence, confidence_notes = get_confidence(row)

    return {
        "score": round(total),
        "reasons": reasons,
        "confidence": confidence,
        "confidence_notes": confidence_notes,
    }


def rank_companies(companies):
    """Score every company and return a table sorted from best to worst."""
    companies = companies.fillna("")  # treat blank cells as empty text
    results = [score_company(row) for _, row in companies.iterrows()]

    ranked = companies.copy()
    ranked["score"] = [r["score"] for r in results]
    ranked["confidence"] = [r["confidence"] for r in results]
    ranked["needs_review"] = ranked["confidence"] == "needs review"
    # Join lists with " | " so each cell stays readable in a CSV.
    ranked["reasons"] = [" | ".join(r["reasons"]) for r in results]
    ranked["confidence_notes"] = [" | ".join(r["confidence_notes"]) for r in results]
    ranked["score_method"] = "rules-based (not AI), assumed criteria"

    # Highest score first. Ties go to the more complete record, then by name.
    order = {"high": 0, "medium": 1, "needs review": 2}
    ranked["_tiebreak"] = ranked["confidence"].map(order)
    ranked = ranked.sort_values(["score", "_tiebreak", "name"], ascending=[False, True, True])
    ranked = ranked.drop(columns="_tiebreak")
    ranked.insert(0, "rank", range(1, len(ranked) + 1))

    columns = [
        "rank", "name", "score", "confidence", "needs_review", "reasons",
        "confidence_notes", "type", "segment", "region", "country", "website",
        "product_categories", "data_completeness", "data_source", "score_method",
    ]
    return ranked[columns]


if __name__ == "__main__":
    companies = pd.read_csv(INPUT_FILE)
    ranked = rank_companies(companies)
    ranked.to_csv(OUTPUT_FILE, index=False)
    print(f"Scored {len(ranked)} companies. Saved to {OUTPUT_FILE}")
    print(ranked[["rank", "name", "score", "confidence"]].to_string(index=False))
