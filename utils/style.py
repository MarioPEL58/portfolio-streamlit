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
            /* 1. Forza sfondo bianco totale ovunque, incluse tutte le pagine successive e i blocchi */
            .stApp, body, html, 
            [data-testid="stAppViewContainer"], 
            [data-testid="stVerticalBlock"],
            [data-testid="stHeader"],
            .main .block-container {
                background-color: white !important;
                background: white !important;
                color: #111111 !important;
            }

            /* 2. GESTIONE GRAFICI PLOTLY MULTIPAGINA */
            /* Evita il reset del filtro di inversione sulle pagine successive */
            .stPlotlyChart, .js-plotly-plot, iframe {
                filter: invert(1) hue-rotate(180deg) !important;
                background: transparent !important;
                visibility: visible !important;
                display: block !important;
                page-break-inside: avoid !important; /* Impedisce che un grafico si spezzi a metà tra due pagine */
                break-inside: avoid !important;
            }

            /* 3. RESET TOTALE TABELLE (st.dataframe / st.table) */
            /* Rimuove lo sfondo nero e forza i bordi e i testi scuri sulle tabelle successive */
            div[data-testid="stDataFrame"], 
            div[data-testid="data-grid"], 
            .stTable, table, th, td, tr {
                background-color: white !important;
                background: white !important;
                color: #111111 !important;
                border-color: #dee2e6 !important;
            }
            
            /* Sbianca le intestazioni delle tabelle di Streamlit */
            thead, th, [role="columnheader"] {
                background-color: #f8f9fa !important;
                color: #111111 !important;
            }

            /* 4. Cambia colore ai testi principali e caption di tutto il report */
            h1, h2, h3, h4, h5, h6, p, span, label, li, 
            .stMarkdown, .stMarkdown p, [data-testid="stCaptionContainer"] {
                color: #111111 !important;
            }

            /* Box delle metriche finanziarie (card delle performance) */
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
