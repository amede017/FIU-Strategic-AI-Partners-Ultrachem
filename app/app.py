"""
app.py: Streamlit interface for the Ultrachem lead intelligence prototype.

IMPORTANT: The data is made-up sample data and the scores are rules-based.
No real AI model runs here. The app reads data/scored_leads.csv only and
makes no external calls. Run src/score.py first to create that file.

Run from the repo root:
    .venv\\Scripts\\python.exe -m streamlit run app/app.py
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
SCORED_FILE = REPO_ROOT / "data" / "scored_leads.csv"

# Import the max points from score.py so the app and scorer never disagree.
# This only reads settings. It does not re-score anything.
sys.path.insert(0, str(REPO_ROOT / "src"))
from score import NO_PRODUCT_MATCH_CAP, WEIGHTS  # noqa: E402

# Plain names for the fields score.py checks for confidence.
FIELD_LABELS = {
    "type": "company type",
    "segment": "segment",
    "region": "region",
    "website": "website",
    "product_categories": "product categories",
}

# High-contrast message boxes. Font size and theme colors are in .streamlit/config.toml.
# Text and background pairs below pass WCAG AA contrast (4.5 to 1 or higher).
STYLE = """
<style>
[data-testid="stTable"] th, [data-testid="stTable"] td { color: #1A1A1A; }
.notice {
    padding: 0.9rem 1.1rem;
    border-radius: 0.5rem;
    border-left: 6px solid;
    margin: 0.5rem 0 1rem 0;
    font-size: 1.05rem;
    line-height: 1.5;
}
.notice-sample { background: #FFF4CE; color: #3D2E00; border-color: #8A6D00; }
.notice-review { background: #FDECEA; color: #5F1A12; border-color: #B42318; }
.notice-ok     { background: #E7F5EC; color: #0B4A26; border-color: #1E7B45; }
.notice-medium { background: #E8F0FB; color: #12325E; border-color: #2E5FA8; }
</style>
"""


def notice(kind, html):
    """Show a colored message box. kind is sample, review, ok, or medium."""
    st.markdown(f'<div class="notice notice-{kind}" role="note">{html}</div>', unsafe_allow_html=True)


def show_sample_banner():
    """The label that the data is sample and scoring is not real AI."""
    notice(
        "sample",
        "<strong>Prototype with sample data.</strong> Every company here is made up. "
        "Scores come from fixed rules, <strong>not real AI</strong>. "
        "The rules are our assumptions until Ultrachem confirms them.",
    )


@st.cache_data
def load_leads():
    """Read the scored leads file and fill blanks with empty text."""
    leads = pd.read_csv(SCORED_FILE)
    text_columns = [c for c in leads.columns
                    if not pd.api.types.is_numeric_dtype(leads[c]) and not pd.api.types.is_bool_dtype(leads[c])]
    return leads.fillna({c: "" for c in text_columns})


def status_label(row):
    """Short status text for the list. The symbol helps readers who cannot see color."""
    if row["needs_review"]:
        return "⚠ Needs review"
    return f"{row['confidence'].capitalize()} confidence"


def review_message(row):
    """Plain-language explanation of why a lead needs review."""
    missing = [FIELD_LABELS.get(f, f) for f in row["missing_fields"].split("; ") if f]
    parts = []
    if missing:
        parts.append("We have no " + " or ".join(missing) + " for this company.")
    parts.append(f"The record's data completeness is <strong>{row['data_completeness'] or 'unknown'}</strong>.")
    parts.append("The score may be wrong. Check the company before you contact it.")
    return "<strong>Needs review.</strong> " + " ".join(parts)


def show_ranked_list(leads, total_count):
    """The ranked table, after filters."""
    st.subheader("Ranked leads")
    review_count = int(leads["needs_review"].sum())
    st.write(f"Showing **{len(leads)} of {total_count}** leads. **{review_count}** need review.")

    table = pd.DataFrame({
        "Rank": leads["rank"],
        "Company": leads["name"],
        "Relative fit score": leads["score"],
        "Status": leads.apply(status_label, axis=1),
        "Segment": leads["segment"],
        "Region": leads["region"],
        "Type": leads["type"],
    })

    def color_status(value):
        if value.startswith("⚠"):
            return "background-color: #FDECEA; color: #5F1A12; font-weight: bold;"
        return ""

    st.dataframe(
        table.style.map(color_status, subset=["Status"]),
        hide_index=True,
        width="stretch",
        height=40 * (len(table) + 1) + 4,  # tall enough to show every row without scrolling
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", width="small"),
            "Relative fit score": st.column_config.ProgressColumn(
                "Relative fit score",
                help="Compares leads in this list from 0 to 100. It is not a chance of closing a deal.",
                min_value=0,
                max_value=100,
                format="%d",
            ),
        },
    )
    st.caption(
        "The relative fit score ranks leads against each other using our assumed rules. "
        "It is not a probability and has not been checked by Ultrachem."
    )


def show_point_breakdown(row):
    """Table of points earned for each part of the score."""
    parts = [
        ("Product fit", "product_points", "product_fit"),
        ("Company type", "type_points", "type_fit"),
        ("Segment", "segment_points", "segment_fit"),
        ("Region", "region_points", "region_fit"),
    ]
    rows = [{"Part": label, "Points earned": int(row[col]), "Points possible": WEIGHTS[w]} for label, col, w in parts]
    subtotal = sum(r["Points earned"] for r in rows)
    rows.append({"Part": "Subtotal", "Points earned": subtotal, "Points possible": sum(WEIGHTS.values())})
    if row["cap_applied"]:
        rows.append({"Part": "Cap: no Ultrachem products match", "Points earned": NO_PRODUCT_MATCH_CAP, "Points possible": ""})
    rows.append({"Part": "Relative fit score", "Points earned": int(row["score"]), "Points possible": 100})
    breakdown = pd.DataFrame(rows).set_index("Part")
    # Text column so the blank on the cap row does not mix with numbers.
    breakdown["Points possible"] = breakdown["Points possible"].astype(str)
    st.table(breakdown)


def show_data_sources(row):
    """Where each piece of data came from."""
    source = row["data_source"]
    if source == "sample":
        source_text = "Made-up sample record from data/sample_companies.csv. Not collected from a real source."
    else:
        source_text = source or "unknown"
    if row["website"]:
        website = f"{row['website']} (fictional address, not visited)"
    else:
        website = "none on record"
    st.markdown(
        f"- **Record source:** {source_text}\n"
        f"- **Website on record:** {website}\n"
        f"- **Product categories on record:** {row['product_categories'] or 'none on record'}\n"
        f"- **Matched Ultrachem categories:** {row['matched_categories'] or 'none'}\n"
        f"- **Data completeness:** {row['data_completeness'] or 'unknown'}\n"
        f"- **Scoring method:** {row['score_method']}"
    )


def show_flag_form(row):
    """Let the user flag wrong data. Flags last only for this browser session."""
    with st.form(key=f"flag_{row['rank']}", clear_on_submit=True):
        note = st.text_area("What looks wrong? (optional)", placeholder="Example: this company stopped selling marine oil.")
        if st.form_submit_button("Flag wrong data"):
            st.session_state.flags.append({
                "Company": row["name"],
                "Note": note.strip() or "(no note)",
                "Time": datetime.now().strftime("%I:%M %p"),
            })
            st.success("Flag recorded for this session. It is not saved to a file.")
    count = sum(1 for f in st.session_state.flags if f["Company"] == row["name"])
    if count:
        st.write(f"This lead has **{count}** flag(s) this session.")


def show_lead_detail(row, total_count):
    """Everything about one lead: score, status, reasons, breakdown, and sources."""
    st.subheader(row["name"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Relative fit score", f"{int(row['score'])} / 100",
                help="Compares leads in this list. It is not a probability.")
    col2.metric("Rank", f"#{int(row['rank'])} of {total_count}")
    col3.metric("Confidence", row["confidence"])

    if row["needs_review"]:
        notice("review", review_message(row))
    elif row["confidence"] == "high":
        notice("ok", "<strong>High confidence.</strong> The record has the key fields we check.")
    else:
        missing = [FIELD_LABELS.get(f, f) for f in row["missing_fields"].split("; ") if f]
        detail = f" Missing: {', '.join(missing)}." if missing else ""
        notice("medium", f"<strong>Medium confidence.</strong> Data completeness is "
                         f"{row['data_completeness']}.{detail}")

    st.markdown("#### Why this score")
    st.markdown("\n".join(f"- {reason}" for reason in row["reasons"].split(" | ")))

    st.markdown("#### Point breakdown")
    show_point_breakdown(row)

    st.markdown("#### Data sources")
    show_data_sources(row)

    st.markdown("#### Report a problem")
    show_flag_form(row)


def main():
    st.set_page_config(page_title="Ultrachem Lead Prototype", layout="wide")
    st.markdown(STYLE, unsafe_allow_html=True)
    if "flags" not in st.session_state:
        st.session_state.flags = []

    st.title("Ultrachem Lead Intelligence")
    show_sample_banner()

    if not SCORED_FILE.exists():
        st.error("data/scored_leads.csv not found. Run: .venv\\Scripts\\python.exe src/score.py")
        st.stop()
    leads = load_leads()

    # Sidebar: filters. The flags list is added at the end of main().
    with st.sidebar:
        st.header("Filters")
        segments = sorted(leads["segment"].unique())
        regions = sorted(leads["region"].unique())
        chosen_segments = st.multiselect("Segment", segments, default=segments)
        chosen_regions = st.multiselect("Region", regions, default=regions)

    filtered = leads[leads["segment"].isin(chosen_segments) & leads["region"].isin(chosen_regions)]
    show_ranked_list(filtered, len(leads))

    st.divider()
    st.subheader("Lead detail")
    if filtered.empty:
        st.info("No leads match these filters. Change the filters in the sidebar.")
    else:
        show_detail_section(filtered, len(leads))

    st.divider()
    show_sample_banner()
    # Drawn last so a flag added on this run shows up right away.
    show_flags_sidebar()


def show_flags_sidebar():
    """List the flags recorded in this browser session."""
    with st.sidebar:
        st.header(f"Flags this session ({len(st.session_state.flags)})")
        if st.session_state.flags:
            for flag in st.session_state.flags:
                st.write(f"**{flag['Company']}** at {flag['Time']}: {flag['Note']}")
        else:
            st.write("No flags yet.")
        st.caption("Flags last only while this browser tab is open.")


def show_detail_section(filtered, total_count):
    """Lead picker plus the detail view for the chosen lead."""
    options = filtered["rank"].tolist()
    # Optional: open a lead directly with ?rank=16 in the URL.
    start = st.query_params.get("rank", "")
    index = options.index(int(start)) if start.isdigit() and int(start) in options else 0
    chosen_rank = st.selectbox(
        "Choose a lead to see details",
        options,
        index=index,
        format_func=lambda r: f"#{r}  {filtered.loc[filtered['rank'] == r, 'name'].iloc[0]}",
    )
    row = filtered[filtered["rank"] == chosen_rank].iloc[0]
    show_lead_detail(row, total_count)


main()
