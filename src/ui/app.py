"""
app.py — PurpleInsight Main Controller
──────────────────────────────────
Pixel-accurate recreation of the 4 screenshot states.

Run: python -m streamlit run src/ui/app.py
"""

import sys, os, uuid, time
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.ui.components.query_input    import render_query_input, render_sidebar_demo_buttons, DEMO_QUERIES
from src.ui.components.chart_renderer import render_chart
from src.ui.components.trust_panel    import render_trust_panel


# ─────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="PurpleInsight",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────────────────────
# Global CSS — matches screenshots precisely
# ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ── Navbar ─────────────────────────────────────────────── */
/* ── Navbar ─────────────────────────────────────────────── */
header[data-testid="stHeader"] {
    background: transparent !important;
    z-index: 999999 !important;
    top: 0 !important;
}
header[data-testid="stHeader"] svg {
    stroke: white !important;
    fill: white !important;
    color: white !important;
}
header[data-testid="stHeader"] span {
    color: white !important;
}

/* ── Custom top navbar ───────────────────────────────────── */
/* ── Custom top navbar ───────────────────────────────────── */
.datatalk-navbar {
    background: #42145f;
    padding-left: 70px;
    padding-right: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 52px;
    z-index: 99;
}
.datatalk-navbar-right {
    padding-right: 60px;
    display: flex;
    align-items: center;
}
.datatalk-navbar-left {
    display: flex;
    align-items: center;
    gap: 10px;
}
.datatalk-logo-badge {
    background: white;
    color: #42145f;
    font-weight: 800;
    font-size: 13px;
    padding: 4px 7px;
    border-radius: 6px;
    letter-spacing: 0.5px;
}
.datatalk-logo-text {
    color: white;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.3px;
}
.datatalk-tagline {
    color: rgba(255,255,255,0.75);
    font-size: 13px;
}

/* ── Sidebar labels ──────────────────────────────────────── */
.sidebar-section-label {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.12em;
    color: #7b4a9f;
    text-transform: uppercase;
    margin: 16px 0 6px;
}

/* ── Demo buttons: active state ──────────────────────────── */
div[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #f0ebf7 !important;
    border-color: #42145f !important;
    color: #42145f !important;
    font-weight: 700;
    border-radius: 6px;
}
div[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: white !important;
    border-color: #ddd !important;
    color: #333 !important;
    border-radius: 6px;
}

/* ── Metric glossary pills ───────────────────────────────── */
.metric-pill {
    display: inline-block;
    background: white;
    border: 1px solid #b39bd1;
    color: #42145f;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
    margin: 2px 3px 2px 0;
}

/* ── Recent queries ──────────────────────────────────────── */
.recent-query-item {
    font-size: 12px;
    color: #555;
    padding: 2px 0;
    cursor: pointer;
}

/* ── Feedback log card ───────────────────────────────────── */
.feedback-log-card {
    background: #f8f6fb;
    border-radius: 8px;
    padding: 10px 12px;
    margin-top: 8px;
}
.feedback-score {
    font-size: 26px;
    font-weight: 800;
    color: #42145f;
}
.feedback-sub {
    font-size: 11px;
    color: #888;
}
.feedback-bar-row {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 4px 0;
    font-size: 11px;
}
.feedback-bar-label { color: #555; min-width: 60px; }
.feedback-bar-track {
    flex: 1;
    height: 5px;
    background: #e0d8ec;
    border-radius: 3px;
    overflow: hidden;
}
.feedback-bar-fill {
    height: 100%;
    background: #42145f;
    border-radius: 3px;
}
.feedback-bar-pct { color: #42145f; font-weight: 700; min-width: 30px; text-align: right; }

/* ── Query type badge ────────────────────────────────────── */
.query-type-badge {
    display: inline-block;
    border: 1.5px solid #d08f4b;
    color: #a35d12;
    background: #fdf5ea;
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 12px;
}

/* ── Answer card ─────────────────────────────────────────── */
.answer-card {
    border-left: 4px solid #42145f;
    padding: 14px 20px;
    margin-bottom: 14px;
    background: #f8f5fb;
    border-radius: 0 8px 8px 0;
}
.answer-headline {
    font-size: 16px;
    font-weight: 700;
    color: #111;
    margin: 0 0 8px;
    line-height: 1.4;
}
.answer-body {
    font-size: 13px;
    color: #444;
    line-height: 1.6;
    margin: 0 0 10px;
}
.answer-impact-label {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.08em;
    color: #4a1f6a;
    text-transform: uppercase;
    margin-bottom: 3px;
}
.answer-impact-text {
    font-size: 12px;
    color: #555;
    font-style: italic;
    margin: 0;
}

/* ── Feedback row ────────────────────────────────────────── */
.feedback-row-card {
    border: 1px solid #e8e0f0;
    border-radius: 8px;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 14px;
    background: white;
}

/* ── Results section ─────────────────────────────────────── */
.results-card {
    border: 1px solid #e8e0f0;
    border-radius: 8px;
    padding: 14px;
    background: white;
    margin-bottom: 14px;
}

/* ── Follow-up suggestions ───────────────────────────────── */
.followup-btn > button {
    background: white !important;
    border: 1px solid #ddd !important;
    color: #333 !important;
    border-radius: 20px !important;
    font-size: 12px !important;
    padding: 4px 14px !important;
}
.followup-btn > button:hover {
    border-color: #42145f !important;
    color: #42145f !important;
}

/* ── Analyse button ──────────────────────────────────────── */
div[data-testid="stMainBlockContainer"] .stButton > button[kind="primary"] {
    background: #42145f !important;
    border-color: #42145f !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    height: 44px !important;
}

/* ── Main query input ────────────────────────────────────── */
div[data-testid="stMainBlockContainer"] .stTextInput > div > input {
    border: 1.5px solid #ddd;
    border-radius: 6px;
    font-size: 14px;
    height: 44px;
    padding: 0 14px;
}
div[data-testid="stMainBlockContainer"] .stTextInput > div > input:focus {
    border-color: #42145f;
    box-shadow: 0 0 0 2px rgba(66,20,95,0.12);
}

/* ── Hide sidebar border ─────────────────────────────────── */
section[data-testid="stSidebar"] { border-right: none; }
[data-testid="stSidebar"] {
    background-color: #fcfbfe !important;
}

/* ── Add padding to block container and sidebar so they aren't hidden by the fixed header ── */
.block-container { padding-top: 3rem !important; }
section[data-testid="stSidebar"] > div { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Mock data — one result per demo query type
# ─────────────────────────────────────────────────────────────

MOCK_RESULTS = {

    "Breakdown": {
        "query_type":   "breakdown",
        "query_label":  "BREAKDOWN",
        "headline":     "Mortgages drive 38.4% of total revenue — nearly double the next product.",
        "body":         "Mortgages generated £48.7M across all regions over 18 months, followed by business accounts at £24.2M (19.1%) and personal loans at £21.8M (17.2%). Credit cards and savings combined account for the remaining 25.3%.",
        "impact":       "Mortgage concentration creates interest rate sensitivity — a 1% rate shift could materially alter the entire revenue mix.",
        "chart": {
            "query_type": "breakdown",
            "x_col":  "product",
            "y_col":  "revenue_m",
            "title":  "Revenue by product type",
            "data": [
                {"product": "Mortgage",     "revenue_m": 48.7},
                {"product": "Business",     "revenue_m": 24.2},
                {"product": "Personal",     "revenue_m": 21.8},
                {"product": "Credit £",     "revenue_m": 15.4},
                {"product": "Savings",      "revenue_m": 10.1},
            ],
            "table": {
                "columns":   ["Product", "Revenue", "Share"],
                "n_rows": 5, "query_ms": 8,
                "rows": [
                    ["mortgage",       "£48.7M", "38.4%"],
                    ["business_acc.",  "£24.2M", "19.1%"],
                    ["personal_loan",  "£21.8M", "17.2%"],
                    ["credit_card",    "£15.4M", "12.1%"],
                    ["savings_acc.",   "£10.1M", " 8.0%"],
                ],
            },
        },
        "trust": {
            "confidence": "High",
            "source":     "monthly_metrics",
            "sql":        "SELECT product_type,\n       ROUND(SUM(revenue)/1e6, 1)          AS revenue_m,\n       ROUND(SUM(revenue)*100.0/SUM(SUM(revenue)) OVER(), 1) AS share_pct\nFROM monthly_metrics\nGROUP BY product_type\nORDER BY revenue_m DESC\nLIMIT 20",
            "metrics":    {"revenue": "Total transaction value credited to the bank (£)", "product_type": "FCA-registered product category"},
            "explanation": "Revenue was aggregated across all regions and 18 months, then normalised as a percentage of total. Mortgage share calculated using SUM(revenue) OVER() window function.",
        },
        "followups": ["Break down by region →", "Mortgage vs credit card trend →", "Monthly mortgage revenue →"],
    },

    "Comparison": {
        "query_type":  "comparison",
        "query_label": "COMPARISON",
        "headline":    "North outperforms South by £3.1M (+26.6%) in 2024 — the largest regional gap in the dataset.",
        "body":        "North generated £14.75M vs South at £11.64M across Jan–Jun 2024. South was severely impacted in Feb–Apr where revenue fell 27.6%, coinciding with churn rising to 9.1%.",
        "impact":      "South's Feb–Apr underperformance risks widening the regional gap further in H2 if retention issues go unaddressed.",
        "chart": {
            "query_type": "comparison",
            "x_col": "month", "y1_col": "north", "y2_col": "south",
            "title": "Monthly revenue — North vs South 2024",
            "data": [
                {"month": "Jan", "north": 2.41, "south": 2.24},
                {"month": "Feb", "north": 2.38, "south": 1.48},
                {"month": "Mar", "north": 2.51, "south": 1.53},
                {"month": "Apr", "north": 2.45, "south": 1.54},
                {"month": "May", "north": 2.52, "south": 2.21},
                {"month": "Jun", "north": 2.48, "south": 2.64},
            ],
            "annotation": {
                "x": "Mar", "y": 1.53,
                "text": "South drop (Feb–Apr)",
                "drop_xs": ["Feb", "Mar", "Apr"],
                "drop_ys": [1.48, 1.53, 1.54],
            },
            "table": {
                "columns": ["Month", "North", "South"],
                "n_rows": 6, "query_ms": 14,
                "anomaly_col": "South", "anomaly_val": "£1.48M",
                "rows": [
                    ["2024-01", "£2.41M", "£2.24M"],
                    ["2024-02", "£2.38M", "£1.48M"],
                    ["2024-03", "£2.51M", "£1.53M"],
                    ["2024-04", "£2.45M", "£1.54M"],
                    ["2024-05", "£2.52M", "£2.21M"],
                    ["2024-06", "£2.48M", "£2.64M"],
                ],
            },
        },
        "trust": {
            "confidence": "High",
            "source":     "monthly_metrics",
            "sql":        "SELECT month,\n       SUM(CASE WHEN region='North' THEN revenue END)/1e6 AS north,\n       SUM(CASE WHEN region='South' THEN revenue END)/1e6 AS south\nFROM monthly_metrics\nWHERE year = 2024\nGROUP BY month\nORDER BY month ASC",
            "metrics":    {"revenue": "Total transaction value credited (£)", "region": "ONS standard UK region"},
            "explanation": "Revenue was pivoted by region using conditional aggregation. Month-over-month comparison uses the same metric definition for both regions to ensure consistency.",
        },
        "followups": ["Why did South drop? →", "All 7 regions →", "South churn trend →"],
    },

    "Change analysis": {
        "query_type":  "change",
        "query_label": "CHANGE ANALYSIS",
        "headline":    "South region revenue fell £543k (−27.6%) in Feb–Apr 2024, driven by a churn spike from 5.3% to 9.1%.",
        "body":        "Revenue dropped from £2.24M in January to £1.48M in February and stayed suppressed through April. Churn jumped simultaneously — pointing to a retention failure, not a seasonal dip.",
        "impact":      "Estimated £1.1M annualised impact if churn remains elevated — equivalent to ~400 customers lost per month.",
        "chart": {
            "query_type": "change",
            "x_col": "month", "y_col": "revenue_m",
            "title": "South region monthly revenue",
            "data": [
                {"month": "Nov", "revenue_m": 2.10},
                {"month": "Dec", "revenue_m": 2.02},
                {"month": "Jan", "revenue_m": 2.24},
                {"month": "Feb", "revenue_m": 1.48},
                {"month": "Mar", "revenue_m": 1.53},
                {"month": "Apr", "revenue_m": 1.54},
                {"month": "May", "revenue_m": 2.21},
            ],
            "annotation": {
                "x0": "Feb", "x1": "Apr",
                "label_x": "Mar", "label_y": 1.35,
                "text": "Drop window (−27.6%)",
                "drop_xs": ["Feb", "Mar", "Apr"],
                "drop_ys": [1.48, 1.53, 1.54],
            },
            "table": {
                "columns": ["Month", "Revenue", "Churn"],
                "n_rows": 7, "query_ms": 11,
                "anomaly_col": "Churn", "anomaly_val": "9.1%",
                "rows": [
                    ["2023-11", "£2.10M", "5.1%"],
                    ["2023-12", "£2.02M", "5.3%"],
                    ["2024-01", "£2.24M", "5.4%"],
                    ["2024-02", "£1.48M", "9.1%"],
                    ["2024-03", "£1.53M", "8.8%"],
                    ["2024-04", "£1.54M", "9.4%"],
                    ["2024-05", "£2.21M", "6.2%"],
                ],
            },
        },
        "trust": {
            "confidence": "High",
            "source":     "monthly_metrics",
            "sql":        "SELECT month, revenue/1e6 AS revenue_m, churn_rate\nFROM monthly_metrics\nWHERE region = 'South'\n  AND year IN (2023, 2024)\nORDER BY month ASC\nLIMIT 20",
            "metrics":    {"churn_rate": "% of active customers who closed their account in the month", "revenue": "Total credited value (£)"},
            "explanation": "Revenue and churn were pulled for the South region across a 7-month window. The drop window was identified by comparing Feb–Apr values against the Jan baseline. Churn spike confirms this is demand-driven, not supply-side.",
        },
        "followups": ["By product in South →", "South vs all regions →", "New customers trend →"],
    },

    "Summary": {
        "query_type":  "summary",
        "query_label": "SUMMARY",
        "headline":    "Customer base grew 4.2% in H1 2024, but churn spiked to 9.4% in April — the highest in 18 months.",
        "body":        "Active customers rose from 182,400 in January to 190,100 by June driven by ~3,200 new customers/month. The notable exception was Feb–Apr where elevated churn offset acquisition gains. Online channel share reached 68% by June, up from 42% a year prior.",
        "impact":      "The Q1 churn event cost ~2,800 customers net — approximately £3.2M in annualised revenue if unaddressed.",
        "chart": {
            "query_type": "summary",
            "x_col": "month", "y1_col": "active", "y2_col": "churn_pct",
            "title": "Active customers & churn — 2024",
            "anomaly_xs": ["Feb", "Mar", "Apr"],
            "data": [
                {"month": "Jan", "active": 182400, "churn_pct": 5.4},
                {"month": "Feb", "active": 180900, "churn_pct": 8.8},
                {"month": "Mar", "active": 179800, "churn_pct": 9.4},
                {"month": "Apr", "active": 181200, "churn_pct": 8.8},
                {"month": "May", "active": 185700, "churn_pct": 6.2},
                {"month": "Jun", "active": 190100, "churn_pct": 5.8},
            ],
            "table": {
                "columns": ["Month", "Active", "Churn", "New"],
                "n_rows": 6, "query_ms": 9,
                "anomaly_col": "Churn", "anomaly_val": "9.4%",
                "rows": [
                    ["Jan", "182,400", "5.4%", "3,100"],
                    ["Feb", "180,900", "8.8%", "2,200"],
                    ["Mar", "179,800", "9.4%", "2,100"],
                    ["Apr", "181,200", "8.8%", "3,600"],
                    ["May", "185,700", "6.2%", "3,500"],
                    ["Jun", "190,100", "5.8%", "3,400"],
                ],
            },
        },
        "trust": {
            "confidence": "High",
            "source":     "monthly_metrics",
            "sql":        "SELECT month,\n       active_customers,\n       churn_rate        AS churn_pct,\n       new_customers\nFROM monthly_metrics\nWHERE year = 2024\nORDER BY month ASC\nLIMIT 12",
            "metrics":    {"active_customers": "Distinct customers with ≥1 transaction in the month", "churn_rate": "% of start-of-month customers who closed account", "new_customers": "First-time account openers in the month"},
            "explanation": "Customer metrics were pulled directly from the monthly_metrics table filtered to 2024. Churn rate uses the standard definition: closures / active_start × 100. New customers are counted on first account-open event.",
        },
        "followups": ["Churn by region →", "Revenue same period →", "Online vs branch shift →"],
    },
}


# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────

METRIC_PILLS = ["revenue", "churn_rate", "active_customers", "avg_transaction_value", "new_customers"]

FEEDBACK_DATA = {
    "score": 82,
    "total": 11,
    "thumbs_up": 9,
    "thumbs_down": 2,
    "by_type": {
        "breakdown": 90,
        "compare":   85,
        "change":    60,
        "summary":  100,
    },
}


def render_sidebar(active_demo: str | None) -> str | None:
    """Renders the full sidebar. Returns a demo query string if a button was clicked."""
    with st.sidebar:

        # Demo queries section
        triggered = render_sidebar_demo_buttons(active_demo)

        # Metric glossary
        st.markdown(
            "<p class='sidebar-section-label'>METRIC GLOSSARY</p>",
            unsafe_allow_html=True,
        )
        pills_html = " ".join(
            f"<span class='metric-pill'>{p}</span>" for p in METRIC_PILLS
        )
        st.markdown(pills_html, unsafe_allow_html=True)

        # Recent queries (only show if there's history)
        history = st.session_state.get("chat_history", [])
        if history:
            st.markdown(
                "<p class='sidebar-section-label'>RECENT QUERIES</p>",
                unsafe_allow_html=True,
            )
            seen = set()
            recent_unique = []
            for entry in reversed(history):
                if entry["query"] not in seen:
                    recent_unique.append(entry)
                    seen.add(entry["query"])
                if len(recent_unique) >= 3:
                    break
            
            for entry in recent_unique:
                short = "🔍 " + (entry["query"][:24] + "..." if len(entry["query"]) > 24 else entry["query"])
                if st.button(short, key=f"recent_{entry['query_id']}_btn", use_container_width=True, type="tertiary"):
                    triggered = entry["query"]

        # Feedback log
        st.markdown(
            "<p class='sidebar-section-label'>FEEDBACK LOG</p>",
            unsafe_allow_html=True,
        )
        fd = FEEDBACK_DATA
        bars_html = "".join([
            f"<div class='feedback-bar-row'>"
            f"<span class='feedback-bar-label'>{k}</span>"
            f"<div class='feedback-bar-track'><div class='feedback-bar-fill' style='width:{v}%'></div></div>"
            f"<span class='feedback-bar-pct'>{v}%</span>"
            f"</div>"
            for k, v in fd["by_type"].items()
        ])

        last_query = ""
        if history:
            last = history[-1]
            icon = "👍" if last.get("feedback") == "positive" else "👎"
            short = last["query"][:22] + "..." if len(last["query"]) > 22 else last["query"]
            last_query = f"<p style='font-size:10px; color:#888; margin:6px 0 0;'>Last: {icon} \"{short}\"</p>"

        st.markdown(
            f"""
            <div class='feedback-log-card'>
                <div style='display:flex; align-items:baseline; gap:6px;'>
                    <span class='feedback-score'>{fd['score']}%</span>
                    <span class='feedback-sub'>helpful</span>
                </div>
                <div style='font-size:10px; color:#888; margin-bottom:8px;'>
                    👍 {fd['thumbs_up']} · 👎 {fd['thumbs_down']} · {fd['total']} total
                </div>
                {bars_html}
                {last_query}
            </div>
            """,
            unsafe_allow_html=True,
        )

    return triggered


# ─────────────────────────────────────────────────────────────
# Answer card renderer
# ─────────────────────────────────────────────────────────────

def render_answer_card(result: dict) -> None:
    """Renders the query-type badge + answer card with headline, body, impact."""
    badge_label = result.get("query_label", "")
    headline    = result.get("headline", "")
    body        = result.get("body", "")
    impact      = result.get("impact", "")

    st.markdown(
        f"<div class='query-type-badge'>{badge_label}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class='answer-card'>
            <p class='answer-headline'>{headline}</p>
            <p class='answer-body'>{body}</p>
            {"<p class='answer-impact-label'>BUSINESS IMPACT</p><p class='answer-impact-text'>" + impact + "</p>" if impact else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Feedback row renderer
# ─────────────────────────────────────────────────────────────

def render_feedback_row(query_id: str) -> None:
    """Renders 'Was this helpful?' + thumbs buttons inline."""
    fb_key = f"feedback_{query_id}"
    fb_val = st.session_state.get(fb_key)

    col_label, col_up, col_down, col_confirm, _ = st.columns([2, 0.5, 0.5, 2, 4])

    with col_label:
        st.markdown(
            "<p style='margin:8px 0; font-size:13px; color:#555;'>Was this helpful?</p>",
            unsafe_allow_html=True,
        )
    with col_up:
        if st.button("👍", key=f"up_{query_id}"):
            st.session_state[fb_key] = "positive"
            st.rerun()
    with col_down:
        if st.button("👎", key=f"dn_{query_id}"):
            st.session_state[fb_key] = "negative"
            st.rerun()
    with col_confirm:
        if fb_val == "positive":
            st.markdown(
                "<span style='background:#d4edda; color:#155724; border-radius:20px; "
                "padding:4px 14px; font-size:12px; font-weight:600;'>👍 Helpful — thank you</span>",
                unsafe_allow_html=True,
            )
        elif fb_val == "negative":
            # Show inline text input for "what went wrong"
            st.text_input(
                "What went wrong?",
                placeholder="e.g. wrong date range · metric seemed off…",
                key=f"fb_note_{query_id}",
                label_visibility="collapsed",
            )


# ─────────────────────────────────────────────────────────────
# Follow-up suggestions
# ─────────────────────────────────────────────────────────────

def render_followups(followups: list[str], result_idx: int) -> None:
    """Renders follow-up query pill buttons at the bottom of each result."""
    if not followups:
        return

    cols = st.columns(len(followups))
    for i, suggestion in enumerate(followups):
        with cols[i]:
            # Strip the → for the actual query
            clean = suggestion.rstrip(" →").strip()
            if st.button(suggestion, key=f"followup_{result_idx}_{i}"):
                st.session_state["prefill_query"] = clean
                st.session_state["auto_query"] = clean
                st.rerun()


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main() -> None:

    # Session state init
    if "chat_history"  not in st.session_state: st.session_state["chat_history"]  = []
    if "active_demo"   not in st.session_state: st.session_state["active_demo"]   = None
    if "prefill_query" not in st.session_state: st.session_state["prefill_query"] = ""

    # Navbar
    st.markdown(
        """
        <div class='datatalk-navbar'>
            <div class='datatalk-navbar-left'>
                <svg width="32" height="32" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
                    <rect width="120" height="120" rx="36" fill="#300d47"/>
                    <g transform="translate(60, 56) scale(1.1)">
                        <path d="M 0,-30 L 17,-20 L 0,-10 L -17,-20 Z" fill="#b062eb"/>
                        <path d="M -17,-20 L 0,-10 L 0,10 L -17,0 Z" fill="#8c3bd4"/>
                        <path d="M 0,-10 L 17,-20 L 17,0 L 0,10 Z" fill="#691da6"/>
                        <path d="M -19,4 L -2,-6 L -19,-16 L -36,-6 Z" fill="#b062eb"/>
                        <path d="M -36,-6 L -19,4 L -19,24 L -36,14 Z" fill="#8c3bd4"/>
                        <path d="M -19,4 L -2,-6 L -2,14 L -19,24 Z" fill="#691da6"/>
                        <path d="M 19,4 L 36,-6 L 19,-16 L 2,-6 Z" fill="#b062eb"/>
                        <path d="M 2,-6 L 19,4 L 19,24 L 2,14 Z" fill="#8c3bd4"/>
                        <path d="M 19,4 L 36,-6 L 36,14 L 19,24 Z" fill="#691da6"/>
                    </g>
                </svg>
                <span class='datatalk-logo-text'>PurpleInsight</span>
            </div>
            <div class='datatalk-navbar-right'>
                <span class='datatalk-tagline'>Self-service banking intelligence</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar
    demo_triggered = render_sidebar(st.session_state.get("active_demo"))
    if demo_triggered:
        st.session_state["prefill_query"] = demo_triggered
        st.session_state["auto_query"] = demo_triggered
        st.rerun()

    # Query input bar
    main_query = render_query_input()
    
    auto_query = st.session_state.pop("auto_query", None)
    query = auto_query or main_query

    # Process query
    if query:
        # Detect which mock result to use based on keywords in the query text
        query_lower = query.lower()
        if any(w in query_lower for w in ["breakdown", "product", "contributes", "makes up"]):
            result = MOCK_RESULTS["Breakdown"]
            st.session_state["active_demo"] = "Breakdown"
        elif any(w in query_lower for w in ["compare", "vs", "north", "south", "region"]):
            result = MOCK_RESULTS["Comparison"]
            st.session_state["active_demo"] = "Comparison"
        elif any(w in query_lower for w in ["why", "drop", "fell", "change", "cause"]):
            result = MOCK_RESULTS["Change analysis"]
            st.session_state["active_demo"] = "Change analysis"
        else:
            result = MOCK_RESULTS["Summary"]
            st.session_state["active_demo"] = "Summary"

        with st.spinner("Analysing…"):
            time.sleep(0.5)

        entry = {
            "query":    query,
            "result":   result,
            "query_id": str(uuid.uuid4())[:8],
        }
        st.session_state["chat_history"].append(entry)

    # Render results — only the most recent one to refresh the main panel
    history = st.session_state.get("chat_history", [])

    if not history:
        st.markdown(
            "<div style='text-align:center; color:#bbb; padding:80px 0; font-size:15px;'>"
            "Select a demo query on the left, or type your own question above."
            "</div>",
            unsafe_allow_html=True,
        )
        return

    latest_entry = history[-1]
    result   = latest_entry["result"]
    query_id = latest_entry.get("query_id", "q_curr")

    # Answer card
    render_answer_card(result)

    # Feedback row
    st.markdown("<div style='border:1px solid #e8e0f0; border-radius:8px; padding:8px 16px; margin-bottom:14px; background:white;'>", unsafe_allow_html=True)
    render_feedback_row(query_id)
    st.markdown("</div>", unsafe_allow_html=True)

    # Chart + table
    st.markdown("<div style='border:1px solid #e8e0f0; border-radius:8px; padding:12px 14px; background:white; margin-bottom:14px;'>", unsafe_allow_html=True)
    render_chart(result.get("chart", {}))
    st.markdown("</div>", unsafe_allow_html=True)

    # Trust panel (collapsible bar)
    render_trust_panel(result.get("trust", {}))

    # Follow-up suggestions
    st.markdown("")
    render_followups(result.get("followups", []), len(history)-1)

    st.markdown("<hr style='border:none; border-top:1px solid #f0e8f8; margin:24px 0;'>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()