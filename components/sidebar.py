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

        use_local_demo = st.checkbox("Usa file locale demo se presente", value=True)

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

        default_start = pd.Timestamp(2026, 3, 1).date()
        min_filter_date = st.date_input("Data minima", value=default_start)

        st.markdown("---")
        st.caption(
            "Per Streamlit Cloud è consigliato usare l'upload del file invece del file locale."
        )

    return {
        "uploaded_file": uploaded_file,
        "use_local_demo": use_local_demo,
        "benchmark": benchmark,
        "show_benchmark": show_benchmark,
        "min_filter_date": min_filter_date,
    }


def resolve_file_source(uploaded_file, use_local_demo: bool):
    if uploaded_file is not None:
        return uploaded_file, uploaded_file.name

    if use_local_demo:
        candidates = [
            Path("portafoglio_query_yf_ETF.xlsx"),
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate, candidate.name

    return None, None
