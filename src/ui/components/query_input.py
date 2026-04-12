"""
query_input.py
──────────────
Renders the top query bar: full-width text input + Analyse button.
Also renders the 4 demo query buttons in the sidebar (called from app.py).
Returns the submitted query string or None.
"""

import streamlit as st

# ── Demo query definitions ────────────────────────────────────
DEMO_QUERIES = {
    "Breakdown":       "What product type contributes most to total revenue?",
    "Comparison":      "Compare North vs South region revenue in 2024",
    "Change analysis": "Why did revenue drop in the South region?",
    "Summary":         "Give me a monthly summary of customer metrics for 2024",
}


def render_sidebar_demo_buttons(active_query_type: str | None) -> str | None:
    """
    Renders the DEMO QUERIES section in the sidebar.
    Returns the query string if a demo button was clicked, else None.
    """
    st.markdown(
        "<p class='sidebar-section-label'>DEMO QUERIES</p>",
        unsafe_allow_html=True,
    )

    triggered = None
    for label, query_text in DEMO_QUERIES.items():
        is_active = (label == active_query_type)
        btn_style = "demo-btn-active" if is_active else "demo-btn"
        # Use a button styled via CSS class
        if st.button(
            label,
            key=f"demo_{label}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            triggered = query_text
            st.session_state["active_demo"] = label

    return triggered


def render_query_input() -> str | None:
    """
    Renders the main query bar (text input + Analyse button).
    Returns the submitted query string, or None.
    """
    prefill = st.session_state.pop("prefill_query", "")

    col_input, col_btn = st.columns([5, 1])

    with col_input:
        query = st.text_input(
            label="query",
            value=prefill,
            placeholder="Ask a question about your banking data...",
            label_visibility="collapsed",
            key="main_query_input",
        )

    with col_btn:
        submitted = st.button(
            "Analyse →",
            type="primary",
            use_container_width=True,
            key="analyse_btn",
        )

    if submitted and query.strip():
        return query.strip()
    if submitted and not query.strip():
        st.warning("Please enter a question first.")
    return None