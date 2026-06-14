from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import pytz

def render_sidebar(create_demo_file):
    with st.sidebar:

        st.markdown("---")
        st.header("Sorgente dati")

        uploaded_file = st.file_uploader(
            "Carica il file Excel",
            type=["xlsx"],
            help="Carica un file Excel con il foglio 'Operazioni' e le colonne richieste."
        )

        st.markdown("---")

        if st.button("🔄 Aggiorna prezzi"):
            st.cache_data.clear()
            st.rerun()

        tz = pytz.timezone("Europe/Rome")
        last_update = datetime.now(tz).strftime("%H:%M:%S %Z")  
        st.caption(f"Ultimo aggiornamento: {last_update}")

        # st.caption(f"Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}")

        st.header("Opzioni")
        benchmark = st.text_input(
            "Ticker benchmark Yahoo (opzionale)",
            value="CSSPX.MI",
            help="Esempio: CSSPX.MI, VWCE.DE, SPY"
        )
        show_benchmark = st.checkbox("Mostra benchmark normalizzato", value=True)

        min_filter_date = st.date_input("Data minima")


    return {
        "uploaded_file": uploaded_file,
        "benchmark": benchmark,
        "show_benchmark": show_benchmark,
        "min_filter_date": min_filter_date,
    }

def resolve_file_source(uploaded_file):
    if uploaded_file is not None:
        return uploaded_file, uploaded_file.name

    return None, None
