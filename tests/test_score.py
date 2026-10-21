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
from score import INPUT_FILE, TARGET_STATE, rank_companies, score_company  # noqa: E402

# Rows in data/sample_companies.csv built as test cases.
THIN_DATA_ROWS = [
    "Tamberly Auto Supply (Sample)",
    "Quarrow Harbor Supply Co (Sample)",
    "Fenwyck Fleet Service Supply (Sample)",
]
DISQUALIFIER_ROWS = {
    "Zephrin Aviation Fluids Supply (Sample)": "aviation_only",
    "Ardlow Lube Distributors (Sample)": "outside_target_state",
    "Bellaquin Quick Lube Centers (Sample)": "not_a_distributor",
    "Hollisby Parts Warehouse (Sample)": "existing_customer",
    "Wrenmoor Janitorial Wholesale (Sample)": "no_product_match",
}
POOR_FIT_HIGH_COMPLETENESS = "Wrenmoor Janitorial Wholesale (Sample)"


@pytest.fixture(scope="module")
def ranked():
    """Score the sample file once for all tests. Does not write any file."""
    return rank_companies(pd.read_csv(INPUT_FILE)).set_index("name")


def make_row(**changes):
    """A complete, strong sample row. Pass keyword arguments to change fields."""
    row = {
        "business_type": "distributor", "distributor_type": "auto parts",
        "city": "Tampa", "state": TARGET_STATE, "website": "test.example", "locations": "6",
        "product_lines": "passenger vehicle oil; coolant", "fluid_brands_carried": "Coralwave",
        "aviation_only": "no", "data_completeness": "high",
    }
    row.update(changes)
    return pd.Series(row)


def test_point_breakdown_sums_to_score(ranked):
    parts = ranked[["product_points", "size_points", "brand_points", "type_points"]].sum(axis=1)
    assert (ranked["score"] == parts).all()


@pytest.mark.parametrize("name,rule", DISQUALIFIER_ROWS.items())
def test_disqualifier_rows_are_disqualified(ranked, name, rule):
    row = ranked.loc[name]
    assert row["status"] == "disqualified"
    assert rule in row["disqualified_by"].split("; ")
    assert row["rank"] == ""                                # not ranked
    assert row["recommended_next_step"].startswith("Do not pursue")


def test_no_disqualified_lead_in_top_10(ranked):
    top_10 = ranked[ranked["rank"].isin(range(1, 11))]
    assert len(top_10) == 10
    assert (top_10["status"] != "disqualified").all()


def test_strong_lead_outside_state_is_still_disqualified():
    # A high score does not save a lead from a disqualifier.
    result = score_company(make_row(
        state="GA",
        product_lines="passenger vehicle oil; gear oil; coolant; antifreeze",
        fluid_brands_carried="Coralwave; Tidemark Oil",
    ))
    assert result["score"] == 100
    assert result["status"] == "disqualified"


def test_blank_fields_never_disqualify():
    # Unknown data should go to review, not be thrown out.
    result = score_company(make_row(state="", product_lines="", aviation_only="", data_completeness="low"))
    assert result["disqualifiers"] == []
    assert result["status"] == "needs review"


def test_aviation_fluid_never_counts_as_a_match():
    result = score_company(make_row(product_lines="aviation fluid; coolant"))
    assert result["matched"] == ["coolant"]


def test_unconfirmed_lines_earn_zero_points():
    result = score_company(make_row(product_lines="hydraulic fluid; agricultural spray oil"))
    assert result["points"]["product_fit"] == 0
    assert "no_product_match" in result["disqualifiers"]


@pytest.mark.parametrize("name", THIN_DATA_ROWS)
def test_thin_data_rows_need_review(ranked, name):
    row = ranked.loc[name]
    assert row["confidence"] == "needs review"
    assert row["status"] == "needs review"
    assert row["recommended_next_step"].startswith("Verify the record")


def test_all_low_completeness_rows_need_review(ranked):
    low = ranked[ranked["data_completeness"] == "low"]
    assert low["needs_review"].all()


def test_poor_fit_with_high_completeness_is_not_flagged_for_review(ranked):
    row = ranked.loc[POOR_FIT_HIGH_COMPLETENESS]
    assert row["data_completeness"] == "high"
    assert row["status"] == "disqualified"  # thrown out with a clear reason
    assert not row["needs_review"]          # but confident, so no review flag


def test_every_ranked_lead_has_why_and_next_step(ranked):
    eligible = ranked[ranked["status"] != "disqualified"]
    assert (eligible["why_attractive"].str.len() > 0).all()
    assert (eligible["recommended_next_step"].str.len() > 0).all()
