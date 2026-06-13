import streamlit as st

 _lang = {}

def set_language(lang_dict):
    global _lang
    _lang = lang_dict

def t(key):
    return _lang.get(key, key)
    import streamlit as st

def init_language(CONFIG):
    if "lang" not in st.session_state:
        st.session_state.lang = "it"

    LANG = st.sidebar.selectbox(
        "Lingua / Language",
        ["it", "en"],
        index=["it", "en"].index(st.session_state.lang)
    )

    st.session_state.lang = LANG
    set_language(CONFIG["lang"][LANG])

    return LANG
