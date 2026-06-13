import streamlit as st
import os
from config.config import load_config
from utils.i18n import set_language, t

CONFIG = load_config()
ENV = os.getenv("ENV", "DEV")

# lingua (per ora semplice, come in app)
LANG = st.sidebar.selectbox("Lingua / Language", ["it", "en"])
set_language(CONFIG["lang"][LANG])

# ===== HEADER =====
st.title(t("help_title"))
st.write(t("help_intro"))

st.divider()

# ===== FUNZIONI =====
st.markdown(f"### {t('help_section_functions')}")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.write(t("help_fun_1"))

with col2:
    with st.container(border=True):
        st.write(t("help_fun_2"))

with col3:
    with st.container(border=True):
        st.write(t("help_fun_3"))

st.divider()

# ===== FILE =====
st.markdown(f"### {t('help_section_file')}")
st.info(f"{t('help_file_desc')}\n\n{t('help_file_cols')}")

st.divider()

# ===== USO =====
st.markdown(f"### {t('help_section_usage')}")

st.write(f"1. {t('help_step_1')}")
st.write(f"2. {t('help_step_2')}")
st.write(f"3. {t('help_step_3')}")
st.write(f"4. {t('help_step_4')}")

st.divider()

st.success(f"💡 {t('help_tip')}")
