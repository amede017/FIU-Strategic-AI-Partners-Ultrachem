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

# Import settings from score.py so the app and scorer never disagree.
# This only reads settings. It does not re-score anything.
sys.path.insert(0, str(REPO_ROOT / "src"))
from score import FIELD_LABELS, TARGET_REGION_NAME, WEIGHTS  # noqa: E402

# The default view shows this many top-ranked leads.
TOP_N = 10

# High-contrast message boxes. Font size and theme colors are in .streamlit/config.toml.
# Text and background pairs below pass WCAG AA contrast (4.5 to 1 or higher).
STYLE = """
<style>
[data-testid="stTable"] th, [data-testid="stTable"] td { color: #1A1A1A; }
/* Streamlit's default gray for captions and placeholders is 4.4 to 1 on the
   sidebar, just under AA. These darker grays pass on white and on the sidebar. */
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: #4D4D4D !important; opacity: 1 !important; }
input::placeholder, textarea::placeholder { color: #595959 !important; opacity: 1; }
[data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapseButton"] * { color: #4D4D4D !important; }
/* Let the filter boxes grow and show full chip names, so no chip is cut off. */
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [role="group"],
[data-testid="stSidebar"] [data-testid="stMultiSelectTagsContainer"] { max-height: none !important; overflow: visible !important; }
[data-testid="stSidebar"] [data-testid="stMultiSelectTagsContainer"] span {
    max-width: none !important; text-overflow: clip !important; overflow: visible !important; white-space: normal !important;
}
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
.notice-dq     { background: #EEEEEE; color: #262626; border-color: #595959; }
.notice-action { background: #FFFFFF; color: #1A1A1A; border-color: #1F4E9C; border: 1px solid #1F4E9C; border-left: 6px solid #1F4E9C; }
</style>
"""


def notice(kind, html):
    """Show a colored message box. kind is sample, review, ok, medium, dq, or action."""
    st.markdown(f'<div class="notice notice-{kind}" role="note">{html}</div>', unsafe_allow_html=True)


def show_sample_banner():
    """The label that the data is sample and scoring is not real AI."""
    notice(
        "sample",
        "<strong>Prototype with sample data.</strong> Every company here is made up. "
        "Scores come from fixed rules, <strong>not real AI</strong>. "
        "The rules are our assumptions until Ultrachem confirms them. "
        f"Target region: {TARGET_REGION_NAME}.",
    )


@st.cache_data
def load_leads():
    """Read the scored leads file and fill blanks with empty text."""
    leads = pd.read_csv(SCORED_FILE)
    # Disqualified leads have a blank rank. Int64 keeps the others as whole numbers.
    leads["rank"] = leads["rank"].astype("Int64")
    text_columns = [c for c in leads.columns
                    if not pd.api.types.is_numeric_dtype(leads[c]) and not pd.api.types.is_bool_dtype(leads[c])]
    return leads.fillna({c: "" for c in text_columns})


def status_label(row):
    """Short status text for the list. The symbol helps readers who cannot see color."""
    if row["status"] == "disqualified":
        return "✕ Disqualified"
    if row["needs_review"]:
        return "⚠ Needs review"
    return f"{row['confidence'].capitalize()} confidence"


def rank_text(row):
    """'3' for a ranked lead, blank for a disqualified one."""
    return "" if pd.isna(row["rank"]) else str(row["rank"])


def review_message(row):
    """Plain-language explanation of why a lead needs review."""
    missing = [FIELD_LABELS.get(f, f) for f in row["missing_fields"].split("; ") if f]
    parts = []
    if missing:
        parts.append("We have no " + " or ".join(missing) + " for this company.")
    parts.append(f"The record's data completeness is <strong>{row['data_completeness'] or 'unknown'}</strong>.")
    parts.append("The score may be wrong. Check the company before you contact it.")
    return "<strong>Needs review.</strong> " + " ".join(parts)


def show_ranked_list(leads, show_all, table_key):
    """The ranked table, after filters. Returns the name of a clicked row, or None."""
    if show_all:
        st.subheader("All leads")
    else:
        st.subheader(f"Top {TOP_N} recommended distributors")
    review_count = int(leads["needs_review"].sum())
    st.write(f"Showing **{len(leads)}** leads. **{review_count}** need review.")
    st.markdown("**Click a row** to open that lead's details below the table.")

    score_help = "Compares leads in this list from 0 to 100. It is not a chance of closing a deal."
    if show_all:
        # This view includes disqualified leads, so the score column is text.
        # The score is still in scored_leads.csv and in the lead detail.
        scores = leads.apply(lambda r: "Not ranked" if r["status"] == "disqualified" else str(r["score"]), axis=1)
        score_column = st.column_config.TextColumn("Relative fit score", help=score_help)
    else:
        # The top 10 view never has disqualified leads, so it keeps the score bars.
        scores = leads["score"]
        score_column = st.column_config.ProgressColumn(
            "Relative fit score", help=score_help, min_value=0, max_value=100, format="%d")

    table = pd.DataFrame({
        "Rank": leads.apply(rank_text, axis=1),
        "Distributor": leads["name"],
        "Relative fit score": scores,
        "Status": leads.apply(status_label, axis=1),
        "Distributor type": leads["distributor_type"],
        "Location": leads.apply(lambda r: ", ".join(p for p in [r["city"], r["state"]] if p), axis=1),
    })

    def color_status(value):
        if value.startswith("⚠"):
            return "background-color: #FDECEA; color: #5F1A12; font-weight: bold;"
        if value.startswith("✕"):
            return "background-color: #EEEEEE; color: #262626; font-weight: bold;"
        return ""

    # Clicking a row reruns the app and reports which row was picked.
    event = st.dataframe(
        table.style.map(color_status, subset=["Status"]),
        key=table_key,
        on_select="rerun",
        selection_mode="single-row",
        hide_index=True,
        width="stretch",
        height=40 * (len(table) + 1) + 4,  # tall enough to show every row without scrolling
        column_config={
            "Rank": st.column_config.TextColumn("Rank", width="small"),
            "Relative fit score": score_column,
        },
    )
    st.caption(
        "The relative fit score ranks leads against each other using our assumed rules. "
        "It is not a probability and has not been checked by Ultrachem. "
        "Disqualified leads are never ranked, whatever their score. "
        "Ties go to the lead with more matched Ultrachem lines, then more complete data, "
        "then company name A to Z."
    )

    rows = event.selection.rows
    if rows and rows[0] < len(table):
        return table.iloc[rows[0]]["Distributor"]
    return None


def show_point_breakdown(row):
    """Table of points earned for each part of the score."""
    parts = [
        ("Product fit", "product_points", "product_fit"),
        ("Size", "size_points", "size_fit"),
        ("Brands carried", "brand_points", "brand_fit"),
        ("Distributor type", "type_points", "type_fit"),
    ]
    rows = [{"Part": label, "Earned": int(row[col]), "Possible": WEIGHTS[w]} for label, col, w in parts]
    if row["status"] == "disqualified":
        rows.append({"Part": "Would have scored", "Earned": int(row["score"]), "Possible": 100})
    else:
        rows.append({"Part": "Relative fit score", "Earned": int(row["score"]), "Possible": 100})
    breakdown = pd.DataFrame(rows).set_index("Part")
    # A narrow column keeps the earned and possible points close together.
    narrow, _ = st.columns([2, 3])
    narrow.table(breakdown)


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
    location = ", ".join(part for part in [row["city"], row["state"]] if part) or "unknown"
    locations = "unknown" if pd.isna(row["locations"]) else str(int(row["locations"]))
    st.markdown(
        f"- **Record source:** {source_text}\n"
        f"- **Website on record:** {website}\n"
        f"- **City and state:** {location}\n"
        f"- **Business type:** {row['business_type'] or 'unknown'}, {row['distributor_type'] or 'unknown'}\n"
        f"- **Locations:** {locations}\n"
        f"- **Product lines on record:** {row['product_lines'] or 'none on record'}\n"
        f"- **Matched Ultrachem lines:** {row['matched_lines'] or 'none'}\n"
        f"- **Fluid brands carried:** {row['fluid_brands_carried'] or 'unknown'} (fictional brand names)\n"
        f"- **Aviation only:** {row['aviation_only'] or 'unknown'}\n"
        f"- **Has a warehouse:** {row['has_warehouse'] or 'unknown'}\n"
        f"- **Has its own sales team:** {row['has_sales_team'] or 'unknown'}\n"
        f"- **Data completeness:** {row['data_completeness'] or 'unknown'}\n"
        f"- **Scoring method:** {row['score_method']}"
    )


def show_flag_form(row):
    """Let the user flag wrong data. Flags last only for this browser session."""
    with st.form(key=f"flag_{row['name']}", clear_on_submit=True):
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


def show_lead_detail(row, ranked_count):
    """Everything about one lead: score, status, next step, reasons, breakdown, and sources."""
    st.subheader(row["name"])

    col1, col2, col3 = st.columns(3)
    if row["status"] == "disqualified":
        col1.metric("Relative fit score", "Not ranked")
        col2.metric("Status", "disqualified")
        col3.metric("Confidence", row["confidence"])
    else:
        col1.metric("Relative fit score", f"{int(row['score'])} / 100",
                    help="Compares leads in this list. It is not a probability.")
        col2.metric("Rank", f"#{row['rank']} of {ranked_count}")
        col3.metric("Confidence", row["confidence"])

    if row["status"] == "disqualified":
        reasons = " ".join(row["disqualify_reasons"].split(" | "))
        notice("dq", f"<strong>Disqualified.</strong> {reasons} "
                     f"Without this rule it would have scored {int(row['score'])} out of 100. "
                     "This lead is not in the recommended list.")
    elif row["needs_review"]:
        notice("review", review_message(row))
    elif row["confidence"] == "high":
        notice("ok", "<strong>High confidence.</strong> The record has the key fields we check.")
    else:
        missing = [FIELD_LABELS.get(f, f) for f in row["missing_fields"].split("; ") if f]
        detail = f" Missing: {', '.join(missing)}." if missing else ""
        notice("medium", f"<strong>Medium confidence.</strong> Data completeness is "
                         f"{row['data_completeness']}.{detail}")

    if row["why_attractive"]:
        st.markdown("#### Why commercially attractive")
        st.markdown(row["why_attractive"])
    st.markdown("#### Recommended next step")
    notice("action", row["recommended_next_step"])
    st.caption("This text comes from fixed templates in src/score.py, not from AI.")

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

    st.title("Ultrachem Distributor Leads")
    show_sample_banner()

    if not SCORED_FILE.exists():
        st.error("data/scored_leads.csv not found. Run: .venv\\Scripts\\python.exe src/score.py")
        st.stop()
    leads = load_leads()
    ranked_count = int(leads["rank"].notna().sum())

    # Sidebar: view and filters. The flags list is added at the end of main().
    with st.sidebar:
        st.header("View")
        show_all = st.toggle("Show all leads, including disqualified", value=False)
        st.header("Filters")
        types = sorted(leads["distributor_type"].unique())
        cities = sorted(leads["city"].unique())
        st.caption("Leave a filter empty to show all.")
        chosen_types = st.multiselect("Distributor type", types, placeholder="All types")
        chosen_cities = st.multiselect("City", cities, placeholder="All cities")

    # Default view: the top ranked leads. Filters then narrow the view.
    in_top = (leads["rank"] <= TOP_N).fillna(False)  # blank rank (disqualified) is never in the top
    shown = leads if show_all else leads[in_top]
    if chosen_types:
        shown = shown[shown["distributor_type"].isin(chosen_types)]
    if chosen_cities:
        shown = shown[shown["city"].isin(chosen_cities)]

    # A new table key per view and filter choice clears an old row click when they change.
    table_key = f"lead_table_{show_all}_" + "|".join(chosen_types + ["/"] + chosen_cities)
    clicked_name = show_ranked_list(shown, show_all, table_key)
    if not show_all:
        more = ranked_count - TOP_N
        dq_count = len(leads) - ranked_count
        st.caption(f"Not shown: {more} lower-ranked leads and {dq_count} disqualified leads. "
                   "Turn on \"Show all leads\" in the sidebar to see them.")

    st.divider()
    st.subheader("Lead detail")
    if shown.empty:
        st.info("No leads match these filters. Change the filters in the sidebar.")
    else:
        show_detail_section(shown, ranked_count, clicked_name)

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


def show_detail_section(shown, ranked_count, clicked_name):
    """Lead picker plus the detail view for the chosen lead.
    The lead can be picked from the dropdown or by clicking a table row.
    Leads are identified by name, because disqualified leads have no rank."""
    options = shown["name"].tolist()

    # First visit: start on the top lead, or on ?rank=9 if it is in the URL.
    if "chosen_name" not in st.session_state:
        start = st.query_params.get("rank", "")
        match = shown[shown["rank"] == int(start)] if start.isdigit() else shown.iloc[0:0]
        st.session_state.chosen_name = match["name"].iloc[0] if len(match) else options[0]
    # A new row click moves the dropdown to that lead.
    if clicked_name is not None and clicked_name != st.session_state.get("last_clicked"):
        st.session_state.chosen_name = clicked_name
    st.session_state.last_clicked = clicked_name
    # If the view or filters hid the chosen lead, fall back to the first lead shown.
    if st.session_state.chosen_name not in options:
        st.session_state.chosen_name = options[0]

    def label(name):
        row = shown[shown["name"] == name].iloc[0]
        return f"Disqualified: {name}" if pd.isna(row["rank"]) else f"#{row['rank']}  {name}"

    chosen_name = st.selectbox("Choose a lead to see details", options, key="chosen_name", format_func=label)
    row = shown[shown["name"] == chosen_name].iloc[0]
    show_lead_detail(row, ranked_count)


main()
