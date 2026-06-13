import streamlit as st
import os

from config.config import load_config
from utils.i18n import init_language, t

# ✅ CONFIG BASE
CONFIG = load_config()
ENV = os.getenv("ENV", "DEV")

env_cfg = CONFIG["env"][ENV]

# ✅ ⚠️ SEMPRE PRIMA DI QUALSIASI st.sidebar
st.set_page_config(
    page_title=env_cfg["title"],
    page_icon=env_cfg["icon"],
    layout="wide"
)

# ✅ ORA puoi usare Streamlit
LANG = init_language(CONFIG)

# ===== UI =====
st.title(t("help_title"))
st.caption(t("help_intro"))

st.divider()

# FUNZIONI
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

# FILE
st.markdown(f"### {t('help_section_file')}")
st.info(f"{t('help_file_desc')}\n\n{t('help_file_cols')}")

st.divider()

# USO
st.markdown(f"### {t('help_section_usage')}")

st.write(f"1. {t('help_step_1')}")
st.write(f"2. {t('help_step_2')}")
st.write(f"3. {t('help_step_3')}")
st.write(f"4. {t('help_step_4')}")

st.divider()

st.success(f"💡 {t('help_tip')}")
