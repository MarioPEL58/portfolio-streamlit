from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import pytz

from utils.i18n import t

def render_sidebar():
    
    options = {
        t("sidebar_label_ticker"): "Ticker",
        t("sidebar_label_name"): "Name"
    }
    with st.sidebar:

        st.markdown("---")
        st.header(t("sidebar_data_source"))

        uploaded_file = st.file_uploader(
            t("sidebar_upload_label"),
            type=["xlsx"],
            help=t("sidebar_upload_help")
        )

        st.markdown("---")

        if st.button(t("sidebar_refresh_button")):
            st.cache_data.clear()
            st.rerun()

        tz = pytz.timezone("Europe/Rome")
        last_update = datetime.now(tz).strftime("%H:%M:%S %Z")
        st.caption(f"{t('sidebar_last_update')}: {last_update}")

        st.header(t("sidebar_options"))
        
        label_choice_ui = st.radio(
            t("sidebar_label_choice_title"),
            list(options.keys()),
            horizontal=True
        )
        
        label_choice = options[label_choice_ui]

        benchmark = st.text_input(
            t("sidebar_benchmark_label"),
            value="CSSPX.MI",
            help=t("sidebar_benchmark_help")
        )

        show_benchmark = st.checkbox(
            t("sidebar_show_benchmark"),
            value=True
        )
        
        use_risk_free= st.sidebar.checkbox(
            t("sidebar_use_risk_free"),
            value=False
        )
        min_filter_date = st.date_input(
            t("sidebar_min_date"),
            value=None
        )

    return {
        "uploaded_file": uploaded_file,
        "benchmark": benchmark,
        "show_benchmark": show_benchmark,
        "use_risk_free": use_risk_free,
        "min_filter_date": min_filter_date,
        "label_choice": label_choice,
    }


def resolve_file_source(uploaded_file):
    if uploaded_file is not None:
        return uploaded_file, uploaded_file.name

    return None, None
