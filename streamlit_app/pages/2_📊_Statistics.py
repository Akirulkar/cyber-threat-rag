# streamlit_app/pages/2_📊_Statistics.py
import streamlit as st
from streamlit_app.api_client import api_client

st.set_page_config(
    page_title="Statistics - Threat Intel AI", page_icon="📊", layout="wide"
)

st.title("📊 Knowledge Base & System Metrics")

with st.spinner("Fetching system statistics..."):
    res = api_client.get_stats()

if res["success"]:
    data = res["data"]

    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="Total Ingested Documents", value=f"{data.get('documents', 0):,}"
        )
        st.metric(label="Vector Store Chunks", value=f"{data.get('chunks', 0):,}")

    with col2:
        st.metric(label="Embedding Model", value=data.get("embedding_model", "N/A"))
        st.metric(label="LLM Engine", value=data.get("llm", "N/A"))

    st.markdown("---")
    st.markdown("### 🗄️ Connected Data Sources")
    st.markdown("- **NVD**: National Vulnerability Database CVE records")
    st.markdown("- **CISA**: Known Exploited Vulnerabilities Catalog")
    st.markdown("- **MITRE ATT&CK**: Adversary Tactics and Techniques")
else:
    st.error(f"Could not load statistics: {res['error']}")
