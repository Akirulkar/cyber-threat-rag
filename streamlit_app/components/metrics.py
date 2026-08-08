# streamlit_app/components/metrics.py
import streamlit as st


def render_metrics(latency_ms: float, retrieved_count: int):
    """Renders RAG pipeline latency and document counts."""
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Latency", value=f"{latency_ms / 1000:.2f} s")
    with col2:
        st.metric(label="Retrieved Contexts", value=f"{retrieved_count} docs")
