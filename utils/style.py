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
            /* 1. Sfondo pagina bianco e testo scuro */
            .stApp, body, html, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
                background-color: white !important;
                background: white !important;
                color: #111111 !important;
            }

            /* 2. GESTIONE GRAFICO DINAMICO PLOTLY */
            /* Non nascondiamo o alteriamo la struttura: applichiamo un filtro di inversione */
            /* che trasforma istantaneamente i tracciati chiari e lo sfondo scuro in bianco/nero */
            .stPlotlyChart, iframe, .js-plotly-plot {
                visibility: visible !important;
                display: block !important;
                filter: invert(1) hue-rotate(180deg) !important;
                background: transparent !important;
            }

            /* Evita blocchi o troncamenti del container interattivo */
            .element-container {
                page-break-inside: avoid !important;
                break-inside: avoid !important;
            }

            /* 3. Box delle performance e metriche */
            [data-testid="stMetric"], div[style*="background-color"] { 
                background-color: #f8f9fa !important;
                border: 1px solid #dee2e6 !important;
                color: #111111 !important;
            }
            
            h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, [data-testid="stCaptionContainer"] {
                color: #111111 !important;
            }

            /* 4. Nascondi elementi inutili della UI */
            [data-testid="stSidebar"], header, footer, .stDeployButton, [data-testid="stDecoration"], .stTabs {
                display: none !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )
