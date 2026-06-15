import streamlit as st

# ✅ variabile globale
_lang = {}

# ✅ funzioni allineate a sinistra (IMPORTANTE)

def set_language(lang_dict):
    global _lang
    _lang = lang_dict


def t(key):
    return _lang.get(key, key)


def init_language(CONFIG):
    if "lang" not in st.session_state:
        st.session_state.lang = "it"

    languages = ["it", "en"]

    LANG = st.sidebar.selectbox(
        "Lingua / Language",
        languages,
        index=languages.index(st.session_state.lang)
    )

    st.session_state.lang = LANG
    set_language(CONFIG["lang"][LANG])

    return LANG
