# streamlit_app/pages/1_💬_Chat.py
import streamlit as st
from streamlit_app.api_client import api_client
from streamlit_app.utils.session import init_session_state, clear_chat_history
from streamlit_app.components.sources import render_sources
from streamlit_app.components.metrics import render_metrics

st.set_page_config(page_title="Chat - Threat Intel AI", page_icon="💬", layout="wide")
init_session_state()

st.title("💬 Threat Intelligence Chat")

# Header action buttons
col_title, col_btn = st.columns([0.8, 0.2])
with col_btn:
    if st.button("Clear Chat", use_container_width=True):
        clear_chat_history()
        st.rerun()

# Display Chat History
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if "sources" in msg:
                render_sources(msg["sources"])
            if "latency_ms" in msg:
                render_metrics(msg["latency_ms"], msg.get("retrieved_documents", 0))

# User Input
if prompt := st.chat_input("Ask about CVE-2024-3094, Cisco vulnerabilities, etc..."):
    # Append user prompt to state
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process query through FastAPI backend
    with st.chat_message("assistant"):
        with st.spinner("Searching threat intelligence knowledge base..."):
            response = api_client.query(question=prompt, top_k=5)

        if response["success"]:
            data = response["data"]
            answer = data["answer"]
            sources = data.get("sources", [])
            latency_ms = data.get("latency_ms", 0.0)
            retrieved_docs = data.get("retrieved_documents", 0)

            st.markdown(answer)
            render_sources(sources)
            render_metrics(latency_ms, retrieved_docs)

            # Store assistant response in history
            st.session_state["messages"].append(
                {
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "latency_ms": latency_ms,
                    "retrieved_documents": retrieved_docs,
                }
            )
        else:
            error_msg = response["error"]
            st.error(error_msg)
            st.session_state["messages"].append(
                {"role": "assistant", "content": f"⚠️ Error: {error_msg}"}
            )
