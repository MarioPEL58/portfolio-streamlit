from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


def render_sidebar():
    with st.sidebar:
        st.title("ℹ️ Guida")

        with st.expander("📊 Cos'è l'app", expanded=False):
            st.write("""
            Questa app ti permette di:
            - ricostruire il valore del portafoglio nel tempo
            - calcolare capitale investito e P/L
            - analizzare allocazione e posizioni correnti
            """)

        with st.expander("📂 Formato file Excel", expanded=False):
            st.write("""
            Il file deve contenere un foglio **Operazioni** (o compatibile)
            con almeno queste colonne:

            - Ticker
            - Data
            - Quantità
            - Prezzo
            - Spese euro
            """)

        with st.expander("▶️ Come usarla", expanded=False):
            st.write("""
            1. Carica il file Excel
            2. Verifica le operazioni lette
            3. Esplora grafici e tabelle
            4. Scarica i CSV finali
            """)

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

        st.caption(f"Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}")

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
