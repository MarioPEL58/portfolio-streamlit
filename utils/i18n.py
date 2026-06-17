import streamlit as st

# ✅ variabile globale
_lang = {}

# ✅ funzioni allineate a sinistra (IMPORTANTE)

def set_language(lang_dict):
    global _lang
    _lang = lang_dict


def t(key):
    return _lang.get(key, key)


# def init_language(CONFIG):
#     if "lang" not in st.session_state:
#         st.session_state.lang = "it"

#     languages = ["it", "en"]

#     LANG = st.sidebar.selectbox(
#         "Lingua / Language",
#         languages,
#         index=languages.index(st.session_state.lang)
#     )

#     st.session_state.lang = LANG
#     set_language(CONFIG["lang"][LANG])

#     return LANG

def init_language(CONFIG):

    languages = list(CONFIG["lang"].keys())

    # =========================
    # ✅ INIT PRIMA VOLTA
    # =========================
    if "lang" not in st.session_state:

        # 1. prova da URL (?lang=en)
        lang_from_url = st.query_params.get("lang")

        if lang_from_url in languages:
            st.session_state.lang = lang_from_url

        else:
            # 2. fallback browser/system (best effort)
            try:
                import locale
                sys_lang = locale.getdefaultlocale()[0]
                sys_lang = sys_lang.split("_")[0].lower() if sys_lang else None
            except:
                sys_lang = None

            if sys_lang in languages:
                st.session_state.lang = sys_lang
            else:
                # 3. fallback finale
                st.session_state.lang = languages[0]  # es: "it"

    # =========================
    # ✅ SELECTOR UI
    # =========================
    LANG = st.sidebar.selectbox(
        "Lingua / Language",
        languages,
        index=languages.index(st.session_state.lang)
    )

    # aggiorna stato
    st.session_state.lang = LANG

    # imposta lingua globale
    set_language(CONFIG["lang"][LANG])

    return LANG
