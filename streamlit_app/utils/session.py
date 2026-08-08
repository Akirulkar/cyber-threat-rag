# streamlit_app/utils/session.py
import streamlit as st


def init_session_state():
    """Initialize persistent variables in Streamlit session state."""
    if "messages" not in st_session_keys():
        st.session_state["messages"] = []
    if "feedback" not in st_session_keys():
        st.session_state["feedback"] = {}


def st_session_keys():
    return st.session_state.keys()


def clear_chat_history():
    """Clear conversation history."""
    st.session_state["messages"] = []
