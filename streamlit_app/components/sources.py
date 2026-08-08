# streamlit_app/components/sources.py
import streamlit as st
from typing import List, Union, Dict, Any


def render_sources(sources: List[Union[str, Dict[str, Any]]]):
    """Renders cited threat intelligence sources inside expandable widgets."""
    if not sources:
        st.caption("No external sources were cited for this response.")
        return

    st.markdown("### 📚 Cited Sources")
    for idx, source in enumerate(sources, 1):
        if isinstance(source, dict):
            doc_id = source.get("document_id", f"Doc {idx}")
            title = source.get("title", "Threat Intelligence Document")
            src_type = source.get("source", "N/A")
            url = source.get("url", "#")

            with st.expander(f"[{src_type}] {doc_id} - {title}"):
                st.write(f"**Source:** {src_type}")
                st.write(f"**Document ID:** {doc_id}")
                if url != "#":
                    st.markdown(f"[View Reference]({url})")
        else:
            with st.expander(f"Source #{idx}"):
                st.write(str(source))
