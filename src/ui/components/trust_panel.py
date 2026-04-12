"""
trust_panel.py
──────────────
Renders the collapsible Trust Panel bar — matching screenshots exactly:

  [Trust panel — every claim is traceable]  [● High confidence ▼]

When expanded, shows:
  • SQL query (code block)
  • Metric definitions applied
  • Data source
  • Explanation
"""

import streamlit as st


_CONF_STYLES = {
    "High":   {"dot": "🟢", "label": "High confidence",   "color": "#155724", "bg": "#d4edda"},
    "Medium": {"dot": "🟡", "label": "Medium confidence", "color": "#856404", "bg": "#fff3cd"},
    "Low":    {"dot": "🔴", "label": "Low confidence",    "color": "#721c24", "bg": "#f8d7da"},
}


def render_trust_panel(trust_data: dict) -> None:
    """
    Renders the collapsible trust panel bar.
    Matches the screenshot: grey bar with confidence badge on the right + ▼ toggle.
    """
    if not trust_data:
        return

    confidence = trust_data.get("confidence", "High")
    style      = _CONF_STYLES.get(confidence, _CONF_STYLES["High"])

    # The outer panel bar — rendered as an expander styled to match the screenshot
    st.markdown(
        f"""
        <style>
        /* Style the trust panel expander to match screenshots */
        div[data-testid="stExpander"] > details > summary {{
            background: #fbf6ff;
            border: 1px solid #e0d8e8;
            border-radius: 6px;
            padding: 10px 16px;
            font-size: 13px;
            font-weight: 600;
            color: #4a0b65;
        }}
        div[data-testid="stExpander"] > details > summary:hover {{
            background: #ede8f5;
        }}
        div[data-testid="stExpander"] > details[open] > summary {{
            border-bottom-left-radius: 0;
            border-bottom-right-radius: 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Confidence badge HTML (shown in the expander label via workaround)
    conf_badge = (
        f"<span style='"
        f"background:{style['bg']}; color:{style['color']}; "
        f"border-radius:20px; padding:3px 10px; font-size:11px; font-weight:600;'>"
        f"● {style['label']}"
        f"</span>"
    )

    with st.expander(
        f"Trust panel — every claim is traceable",
        expanded=False,
    ):
        # Confidence + source row
        col_conf, col_src = st.columns([1, 2])
        with col_conf:
            st.markdown(
                f"<div style='margin-top:4px;'>{conf_badge}</div>",
                unsafe_allow_html=True,
            )
        with col_src:
            source = trust_data.get("source", "")
            if source:
                st.markdown(
                    f"<p style='font-size:12px; color:#555; margin:6px 0;'>"
                    f"📁 <code>{source}</code></p>",
                    unsafe_allow_html=True,
                )

        st.markdown("")

        # SQL block
        sql = trust_data.get("sql", "")
        if sql:
            st.markdown(
                "<p style='font-size:12px; font-weight:600; color:#4a0b65; margin-bottom:4px;'>"
                "SQL executed</p>",
                unsafe_allow_html=True,
            )
            st.code(sql, language="sql")
            st.caption("Raw data rows were never exposed to the AI — only aggregated query results.")

        # Metric definitions
        metrics = trust_data.get("metrics", {})
        if metrics:
            st.markdown(
                "<p style='font-size:12px; font-weight:600; color:#4a0b65; margin:12px 0 4px;'>"
                "Metric definitions applied</p>",
                unsafe_allow_html=True,
            )
            for term, defn in metrics.items():
                st.markdown(
                    f"<p style='font-size:12px; margin:2px 0;'>"
                    f"<code>{term}</code> — {defn}</p>",
                    unsafe_allow_html=True,
                )

        # Explanation
        explanation = trust_data.get("explanation", "")
        if explanation:
            st.markdown(
                "<p style='font-size:12px; font-weight:600; color:#4a0b65; margin:12px 0 4px;'>"
                "How this answer was derived</p>",
                unsafe_allow_html=True,
            )
            st.info(explanation, icon="💡")