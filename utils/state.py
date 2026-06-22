import streamlit as st

def init_state(defaults: dict):
    """Inizializza lo stato globale una sola volta"""
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_state(key, default=None):
    return st.session_state.get(key, default)


def set_state(key, value):
    st.session_state[key] = value


def reset_state(keys: list[str] | None = None):
    """Reset selettivo (utile per refresh controllati)"""
    if keys is None:
        st.session_state.clear()
    else:
        for k in keys:
            if k in st.session_state:
                del st.session_state[k]
