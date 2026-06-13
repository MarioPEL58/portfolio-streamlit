import streamlit as st
import os

from config.config import load_config
from utils.i18n import set_language, t

CONFIG = load_config()
ENV = os.getenv("ENV", "DEV")

# stessa lingua della app
LANG = st.sidebar.selectbox("Lingua / Language", ["it", "en"])
set_language(CONFIG["lang"][LANG])

st.title("ℹ️ Guida")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 Funzioni")
    st.markdown("""
    - Andamento portafoglio  
    - Capitale investito  
    - Profit & Loss  
    - Allocazione  
    """)

    st.markdown("### 📂 File Excel")
    st.markdown("""
    Foglio **Operazioni**:
    - Ticker  
    - Data  
    - Quantità  
    - Prezzo  
    - Spese  
    """)

with col2:
    st.markdown("### ▶️ Come usarla")
    st.markdown("""
    1. Carica Excel  
    2. Controlla dati  
    3. Analizza  
    4. Esporta CSV  
    """)

    st.info("💡 Controlla sempre i dati dopo il caricamento")
