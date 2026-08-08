# streamlit_app/pages/3_⚙️_Admin.py
import streamlit as st

st.set_page_config(page_title="Admin - Threat Intel AI", page_icon="⚙️", layout="wide")

st.title("⚙️ System Administration")

st.warning(
    "🔒 Administrative functions are restricted. Operations triggered here affect the core index."
)

st.subheader("Index Maintenance")
col1, col2 = st.columns(2)

with col1:
    if st.button("Rebuild Vector Store Index", use_container_width=True):
        st.info("Triggering vector index rebuild job...")

with col2:
    if st.button("Trigger Data Ingestion Pipeline", use_container_width=True):
        st.info("Triggering ingestion from NVD & CISA...")
