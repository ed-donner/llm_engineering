"""Executive summary display components."""

from __future__ import annotations

from typing import Dict, Optional

import streamlit as st


def render_summary(summary: Optional[Dict[str, str]]) -> None:
    """Render executive summary card."""
    st.subheader("Executive Summary", anchor=False)
    if not summary:
        st.warning("Executive summary disabled. Provide an OpenAI API key to unlock this section.", icon="🤖")
        return
    st.markdown(
        """
        <div style="padding:1rem;border:1px solid #eee;border-radius:0.75rem;background-color:#f9fafb;">
        """,
        unsafe_allow_html=True,
    )
    st.markdown(summary.get("raw", ""))
    st.markdown("</div>", unsafe_allow_html=True)
