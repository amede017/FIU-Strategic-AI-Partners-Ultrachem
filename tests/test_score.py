"""
Tests for src/score.py. They check the scoring rules, not whether the
rules are right for Ultrachem. The rules are still assumptions.

Run from the repo root:
    .venv\\Scripts\\python.exe -m pytest
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
from score import INPUT_FILE, NO_PRODUCT_MATCH_CAP, rank_companies, score_company  # noqa: E402

# Rows in data/sample_companies.csv built as test cases.
THIN_DATA_ROWS = [
    "Harbor Route Transit Repair (Sample)",  # row 7: no website
    "Northbay Plant Services (Sample)",      # row 11: name and region only
    "Coral Keel Outboard Works (Sample)",    # row 14: little product detail
]
POOR_FIT_HIGH_COMPLETENESS = "Maple Lane Janitorial Wholesale (Sample)"  # row 20


@pytest.fixture(scope="module")
def ranked():
    """Score the sample file once for all tests. Does not write any file."""
    return rank_companies(pd.read_csv(INPUT_FILE)).set_index("name")


def test_point_breakdown_sums_to_score(ranked):
    parts = ranked[["product_points", "type_points", "segment_points", "region_points"]].sum(axis=1)
    for name, row in ranked.iterrows():
        if row["cap_applied"]:
            # Capped rows: the parts add up to more than the cap, and the score is the cap.
            assert parts[name] > NO_PRODUCT_MATCH_CAP, name
            assert row["score"] == NO_PRODUCT_MATCH_CAP, name
        else:
            assert row["score"] == parts[name], name


def test_no_match_cap_holds(ranked):
    no_match = ranked[ranked["matched_count"] == 0]
    assert len(no_match) > 0, "sample data should include rows with no product match"
    assert (no_match["score"] <= NO_PRODUCT_MATCH_CAP).all()


def test_no_match_cap_holds_for_best_possible_other_fields():
    # Perfect type, segment, and region, but sells nothing Ultrachem makes.
    row = pd.Series({
        "type": "distributor", "segment": "distributor", "region": "US Southeast",
        "website": "test.example", "product_categories": "office supplies",
        "data_completeness": "high",
    })
    result = score_company(row)
    assert result["score"] == NO_PRODUCT_MATCH_CAP
    assert result["cap_applied"]


@pytest.mark.parametrize("name", THIN_DATA_ROWS)
def test_thin_data_rows_need_review(ranked, name):
    assert ranked.loc[name, "confidence"] == "needs review"
    assert ranked.loc[name, "needs_review"]


def test_all_low_completeness_rows_need_review(ranked):
    low = ranked[ranked["data_completeness"] == "low"]
    assert low["needs_review"].all()


def test_poor_fit_with_high_completeness_is_not_flagged(ranked):
    row = ranked.loc[POOR_FIT_HIGH_COMPLETENESS]
    assert row["data_completeness"] == "high"
    assert row["score"] <= NO_PRODUCT_MATCH_CAP  # low score
    assert not row["needs_review"]               # but confident, so no review flag
