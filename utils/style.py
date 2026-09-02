# utils/style.py
import streamlit as st

def applica_stile_stampa():
    """
    Inietta il CSS necessario per convertire la dashboard 
    in un layout ottimizzato per la stampa (sfondo bianco) quando si preme Ctrl+P.
    """
    st.markdown(
        """
        <style>
        @media print {
            /* 1. Sfondo bianco totale e testo scuro */
            .stApp, body, html, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
                background-color: white !important;
                background: white !important;
                color: #111111 !important;
            }

            /* 2. Ottimizzazione delle metriche e dei box colorati (es. rossi/verdi) */
            [data-testid="stMetric"], div[style*="background-color"] { 
                background-color: #f8f9fa !important;
                border: 1px solid #dee2e6 !important;
                color: #111111 !important;
                border-radius: 4px;
            }
            
            /* Forza il testo nero per titoli e testi generici */
            h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {
                color: #111111 !important;
            }

            /* 3. Nasconde i componenti dell'interfaccia web inutili su carta */
            [data-testid="stSidebar"], header, footer, .stDeployButton, [data-testid="stDecoration"], .stTabs {
                display: none !important;
            }
            
            /* Evita l'interruzione di pagina a metà di un grafico o di un blocco */
            .element-container, column {
                page-break-inside: avoid !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )
