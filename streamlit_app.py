import streamlit as st
import httpx
import os
from pathlib import Path

API_URL = os.getenv("CONTINUUM_API_URL", "http://localhost:8000")


def _load(filename: str) -> str:
    """Load a static file from app/static/."""
    return Path(f"app/static/{filename}").read_text()


def chat_html(api_url: str) -> str:
    css  = _load("chat.css")
    html = _load("chat.html")
    js   = _load("chat.js")
    return f"""
<style>{css}</style>
{html}
<script>
window.CONTINUUM_API_URL = "{api_url}";
{js}
</script>
"""


st.set_page_config(page_title="Continuum", layout="centered")

tab1, tab2 = st.tabs(["Find Care", "MTTR Dashboard"])

with tab1:
    st.components.v1.html(
        chat_html(API_URL),
        height=750,
        scrolling=True
    )

with tab2:
    st.subheader("MTTR Dashboard")
    st.caption("Live routing metrics. Use Find Care tab to generate data.")

    try:
        data = httpx.get(f"{API_URL}/api/v1/metrics", timeout=10).json()

        if data.get("total_requests", 0) == 0:
            st.info("No routing requests yet. Use Find Care tab to generate metrics.")
        else:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Requests",  data["total_requests"])
            col2.metric("Avg MTTR",        f"{data['avg_mttr_seconds']}s")
            col3.metric("Leakage Rate",    f"{round(data['leakage_rate']*100,1)}%")
            col4.metric("Deflection Rate", f"{round(data['agentic_deflection_rate']*100,1)}%")

            st.divider()

            col1, col2, col3 = st.columns(3)
            col1.metric("Resolved",          data["resolved_count"])
            col2.metric("P95 MTTR",          f"{data['p95_mttr_seconds']}s")
            col3.metric("Pharmacy Coverage", f"{round(data['pharmacy_coverage_rate']*100,1)}%")
            st.caption(f"Last updated: {data.get('last_updated', 'N/A')}")

            recent = httpx.get(
                f"{API_URL}/api/v1/metrics/recent", timeout=10
            ).json()

            if recent:
                st.subheader("Recent Requests")
                for r in reversed(recent):
                    with st.container(border=True):
                        col1, col2, col3 = st.columns(3)
                        col1.markdown(f"**{'Resolved' if r['resolved'] else 'Unresolved'}**")
                        col2.markdown(f"MTTR: **{r['mttr_seconds']}s**")
                        col3.markdown(f"Routed to: **{r['routed_to']}**")

    except Exception as e:
        st.error(f"Could not load metrics: {str(e)}")

    if st.button("Reset Metrics"):
        try:
            httpx.delete(f"{API_URL}/api/v1/metrics/reset", timeout=10)
            st.success("Metrics reset.")
            st.cache_data(clear)
        except Exception as e:
            st.error(f"Error: {str(e)}")