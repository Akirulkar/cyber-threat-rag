# streamlit_app/app.py
import streamlit as st
from streamlit_app.api_client import api_client
from streamlit_app.utils.session import init_session_state

st.set_page_config(
    page_title="Cyber Threat Intelligence Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()

# Sidebar Navigation & Backend Status
st.sidebar.title("🛡️ Threat Intel AI")
st.sidebar.markdown("---")

# Health indicator
is_online = api_client.health_check()
if is_online:
    st.sidebar.success("Backend: Connected (FastAPI)")
else:
    st.sidebar.error("Backend: Disconnected")

st.sidebar.markdown("---")
st.sidebar.info("Navigate through pages using the menu above.")

st.title("Cybersecurity Threat Intelligence Assistant")
st.markdown(
    "Ask questions about CVEs, threat actors, attack vectors, or mitigation strategies."
)

# Redirect home page directly to main chat interface
st.switch_page("pages/1_💬_Chat.py")
