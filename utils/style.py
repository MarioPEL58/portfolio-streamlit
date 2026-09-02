# utils/style.py
import streamlit as st

# def applica_stile_stampa():
#     """
#     Inietta il CSS necessario per convertire la dashboard 
#     in un layout ottimizzato per la stampa (sfondo bianco) quando si preme Ctrl+P.
#     """
    
#     st.markdown(
#         """
#         <style>
#         @media print {
#             /* 1. Sfondo pagina bianco e testo scuro */
#             .stApp, body, html, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
#                 background-color: white !important;
#                 background: white !important;
#                 color: #111111 !important;
#             }

#             /* 2. GESTIONE GRAFICO DINAMICO PLOTLY */
#             /* Non nascondiamo o alteriamo la struttura: applichiamo un filtro di inversione */
#             /* che trasforma istantaneamente i tracciati chiari e lo sfondo scuro in bianco/nero */
#             .stPlotlyChart, iframe, .js-plotly-plot {
#                 visibility: visible !important;
#                 display: block !important;
#                 filter: invert(1) hue-rotate(180deg) !important;
#                 background: transparent !important;
#             }

#             /* Evita blocchi o troncamenti del container interattivo */
#             .element-container {
#                 page-break-inside: avoid !important;
#                 break-inside: avoid !important;
#             }

#             /* 3. Box delle performance e metriche */
#             [data-testid="stMetric"], div[style*="background-color"] { 
#                 background-color: #f8f9fa !important;
#                 border: 1px solid #dee2e6 !important;
#                 color: #111111 !important;
#             }
            
#             h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, [data-testid="stCaptionContainer"] {
#                 color: #111111 !important;
#             }

#             /* 4. Nascondi elementi inutili della UI */
#             [data-testid="stSidebar"], header, footer, .stDeployButton, [data-testid="stDecoration"], .stTabs {
#                 display: none !important;
#             }
#         }
#         </style>
#         """,
#         unsafe_allow_html=True
#     )

def applica_stile_stampa():
    st.markdown(
        """
        <style>
        /* Isola le regole SOLO per il momento della stampa fisica */
        @media print {
            
            /* 1. Forza sfondo bianco su tutta l'applicazione (tutte le pagine del PDF) */
            html, body, .stApp, [data-testid="stAppViewContainer"] {
                background-color: white !important;
                background: white !important;
                color: #111111 !important;
            }

            /* 2. FILTRO GRAFICO (Il tuo blocco originale che funzionava perfettamente) */
            .stPlotlyChart {
                filter: invert(1) hue-rotate(180deg) !important;
                background: transparent !important;
                visibility: visible !important;
                display: block !important;
            }

            /* Evita che i grafici si spezzino a metà tra la pagina 1 e la pagina 2 */
            .stPlotlyChart, .element-container {
                page-break-inside: avoid !important;
                break-inside: avoid !important;
            }

            /* 3. SBANCAMENTO TABELLE E DATAFRAME */
            /* Forza le tabelle successive a ereditare il fondo bianco e testo nero */
            div[data-testid="stDataFrame"], .stTable, table, tr, td, th {
                background-color: white !important;
                background: white !important;
                color: #111111 !important;
                border-color: #dee2e6 !important;
            }

            /* 4. Forza tutti i testi principali, markdown e didascalie a essere scuri */
            h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, [data-testid="stCaptionContainer"] {
                color: #111111 !important;
            }

            /* Box delle metriche finanziarie convertiti in chiaro */
            [data-testid="stMetric"], div[style*="background-color"] { 
                background-color: #f8f9fa !important;
                border: 1px solid #dee2e6 !important;
                color: #111111 !important;
            }

            /* 5. Nasconde la sidebar e i menu di controllo nel PDF finale */
            [data-testid="stSidebar"], header, footer, .stDeployButton, [data-testid="stDecoration"] {
                display: none !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def applica_layout_stampa_chiaro(fig):
    """
    Converte la dashboard in modalità chiara per la stampa:
    1. Imposta nativamente il template chiaro sul grafico Plotly.
    2. Inietta il CSS per forzare lo sfondo bianco e scurire i testi.
    """
    # Ridisegna le linee del grafico in scuro su sfondo bianco nativo
    fig.update_layout(template="plotly_white")
    
    # Inietta il CSS per la pagina web
    st.markdown(
        """
        <style>
        /* 1. Forza sfondo bianco totale sulla pagina principale */
        .stApp, body, html, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: white !important;
            background: white !important;
            color: #111111 !important;
        }
        
        /* 2. Forza tutti i testi del report a diventare scuri */
        h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, [data-testid="stCaptionContainer"] {
            color: #111111 !important;
        }
        
        /* 3. Converte i box delle performance (metriche) in riquadri chiari puliti */
        [data-testid="stMetric"], div[style*="background-color"] { 
            background-color: #f8f9fa !important;
            border: 1px solid #dee2e6 !important;
            color: #111111 !important;
            border-radius: 4px;
        }
        
        /* 4. Regola specifica per l'azione di stampa del browser (Ctrl+P / Menu Print) */
        @media print {
            /* Nasconde la barra laterale e i menu per non averli sul foglio PDF */
            [data-testid="stSidebar"], header, footer, .stDeployButton, [data-testid="stDecoration"] {
                display: none !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )
