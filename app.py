import os
import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from components.sidebar import render_sidebar, resolve_file_source
from components.charts import portfolio_chart
from components.charts import allocation_pie_chart, allocation_bar_chart
from components.operations_preview import render_operations_preview

from services.excel_loader import load_dividends_from_excel, load_operations_from_excel
from services.market_data import download_close_prices
from services.portfolio import build_portfolio
from utils.formatting import fmt_eur, fmt_pct, style_pl_column
from utils.demo import create_demo_file

from utils.kpi_cards import (
    render_value_card,
    render_unrealized_card,
    render_realized_card,
    render_total_pl_card
)

ENV = os.getenv("ENV", "DEV")

CONFIG = {
    "DEV": {
        "title": "🚧 DEV Portfolio Tracker",
        "icon": "🚧"
    },
    "PROD": {
        "title": "Portfolio Tracker ETF / Azioni",
        "icon": "📈"
    }
}

cfg = CONFIG.get(ENV, CONFIG["DEV"])

st.set_page_config(
    page_title=cfg["title"],
    page_icon=cfg["icon"],
    layout="wide"
)

# ENV check 

if ENV == "DEV":
    st.title("🚧 DEV Portfolio Tracker ETF / Azioni")
    st.warning("⚠️ Ambiente di sviluppo")
else:
    st.title("📈 Portfolio Tracker ETF / Azioni")

st.caption(
    "Carica un file Excel con il foglio Operazioni e ricostruisci il valore del portafoglio nel tempo."
)

# Sidebar
sidebar_cfg = render_sidebar(create_demo_file)
uploaded_file = sidebar_cfg["uploaded_file"]
use_local_demo = sidebar_cfg["use_local_demo"]
benchmark = sidebar_cfg["benchmark"]
show_benchmark = sidebar_cfg["show_benchmark"]
min_filter_date = sidebar_cfg["min_filter_date"]

# Input source
file_source, file_label = resolve_file_source(uploaded_file, use_local_demo)

if file_source is None:
    st.info("Carica un file Excel per iniziare.")
    st.stop()

# Load data
try:
    ops = load_operations_from_excel(file_source)
    dividends = load_dividends_from_excel(file_source)
except Exception as e:
    st.error(f"Errore nel caricamento del file: {e}")
    st.stop()

ops = ops[ops["Data"] >= pd.Timestamp(min_filter_date)]
if ops.empty:
    st.warning("Nessuna operazione disponibile dopo la data minima selezionata.")
    st.stop()

st.success(f"File caricato: {file_label}")

# =========================
# 🎛️ FILTRI GLOBALI
# =========================
st.markdown("### 🎛️ Filtri")

col1, col2 = st.columns(2)

# -------------------------
# ✅ Intermediario
# -------------------------
with col1:
    all_brokers = sorted(
        ops["Intermediario"].dropna().astype(str).str.strip().unique().tolist()
    )

    selected_brokers = st.multiselect(
        "Intermediari",
        options=all_brokers,
        default=all_brokers
    )

# -------------------------
# ✅ Tipo
# -------------------------
with col2:
    all_types = sorted(
        ops["Tipo"].dropna().astype(str).str.strip().unique().tolist()
    )

    selected_types = st.multiselect(
        "Tipo",
        options=all_types,
        default=all_types
    )

# =========================
# ✅ FILTRO OPERAZIONI
# =========================
ops_filtered = ops.copy()

if selected_brokers:
    ops_filtered = ops_filtered[
        ops_filtered["Intermediario"].astype(str).str.strip().isin(selected_brokers)
    ]

if selected_types:
    ops_filtered = ops_filtered[
        ops_filtered["Tipo"].astype(str).str.strip().isin(selected_types)
    ]

ops_filtered = ops_filtered.copy()

# =========================
# ✅ 2. CREA dividends_filtered (DOPO)
# =========================
if dividends is not None and not dividends.empty:
    # ✅ normalizzo ID OPS
    ops_ids = (
        ops_filtered["ID"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.replace(".0", "", regex=False)
    )

    # ✅ normalizzo ID DIVIDENDI
    dividends_filtered = dividends.copy()
    dividends_filtered["ID"] = (
        dividends_filtered["ID"]
        .astype(str)
        .str.strip()
        .str.replace(".0", "", regex=False)
    )

    # ✅ filtro corretto
    dividends_filtered = dividends_filtered[
        dividends_filtered["ID"].isin(ops_ids)
    ].copy()
else:
    dividends_filtered = dividends


# =========================
# ✅ FEEDBACK UX
# =========================

# ✅ filtro attivo
active_filters_details = []

if set(selected_brokers) != set(all_brokers):
    active_filters_details.append(f"Intermediari ({', '.join(selected_brokers)})")

if set(selected_types) != set(all_types):
    active_filters_details.append(f"Tipo ({', '.join(selected_types)})")

if active_filters_details:
    st.caption(f"Filtri attivi: {', '.join(active_filters_details)}")


# ✅ dividendi mancanti (solo se esistono ma filtrati via)
if dividends is not None and not dividends.empty:
    if dividends_filtered is not None and dividends_filtered.empty:
        st.caption("ℹ️ Nessun dividendo per il filtro selezionato")

# Price download
start_date = ops["Data"].min().normalize()
end_date = pd.Timestamp.today().normalize()

closes, missing = download_close_prices(
    sorted(ops["Ticker"].unique().tolist()),
    start_date,
    end_date
)

if closes.empty:
    st.error("Non sono riuscito a scaricare i prezzi da Yahoo Finance.")
    st.stop()

if missing:
    st.warning("Ticker senza prezzi scaricati: " + ", ".join(missing))

# Portfolio
series, current, holdings, exposure, ops_enriched = build_portfolio(ops_filtered, closes, dividends_filtered)

if series.empty:
    st.error("Non è stato possibile costruire il portafoglio con i dati disponibili.")
    st.stop()

render_operations_preview(ops_enriched)
# with st.expander("Anteprima operazioni", expanded=False):
#    st.dataframe(ops_enriched, use_container_width=True)

# Benchmark
bench_norm = None
if show_benchmark and benchmark.strip():
    bench_df, _ = download_close_prices(
        [benchmark.strip()],
        start_date,
        end_date
    )

    if not bench_df.empty and benchmark.strip() in bench_df.columns:
        b = bench_df[benchmark.strip()].dropna()
        if not b.empty and b.iloc[0] != 0:
            bench_norm = abs(series["Capitale investito"].iloc[-1]) * (b / b.iloc[0])

# =========================
# KPIs
# =========================

latest_value = float(series["Valore portafoglio"].iloc[-1])
latest_invested = float(series["Capitale investito"].iloc[-1])
latest_pnl = float(series["P/L totale"].iloc[-1])
latest_daily_pl = float(series["P/L Giornaliero"].iloc[-1])
latest_daily_pl_pct = float(series["P/L Giornaliero %"].iloc[-1])

latest_pnl_pct = latest_pnl / abs(latest_invested) if latest_invested != 0 else np.nan

latest_realized = float(series["P/L realizzato"].iloc[-1])
latest_dividends = float(series["Dividendi netti"].sum())



# =========================
# ✅ Realized % (NUOVO METODO)
# =========================

# usa ops CF già arricchite dal motore
sell_ops = ops_enriched.loc[ops_enriched["Quantita"] < 0].copy()

if not sell_ops.empty:
    realized_cost = (
        sell_ops["Quantita"].abs() * sell_ops["AvgCostBefore"]
    ).sum()

    latest_realized_pct = (
        latest_realized / realized_cost if realized_cost != 0 else np.nan
    )
else:
    latest_realized_pct = np.nan
# =========================
# ✅ Breakdown P/L
# =========================

sell_ops = ops_enriched.loc[ops_enriched["Quantita"] < 0].copy()

realized_trading = (
    sell_ops["RealizedTradePL"].sum()
    if not sell_ops.empty else 0.0
)

realized_dividends = float(series["Dividendi netti"].sum())

realized_total = realized_trading + realized_dividends

unrealized_pl = latest_pnl - realized_total

if latest_invested != 0:
    unrealized_pct = unrealized_pl / abs(latest_invested)
else:
    unrealized_pct = None

start_date = series.index.min()
end_date = series.index.max()

days = (end_date - start_date).days

if days > 5 and latest_pnl_pct is not None:
    annualized_pct = (1 + latest_pnl_pct) ** (365.25 / days) - 1
else:
    annualized_pct = None

# =========================
# UI KPI
# =========================

# k1, k2, k3, k4 = st.columns(4)

# k1.metric("Valore portafoglio", fmt_eur(latest_value))
# k2.metric("Capitale investito", fmt_eur(latest_invested))
# k3.metric("Posizioni aperte", len(current))
# k4.metric("Dividendi netti", fmt_eur(latest_dividends))

# k5, k6, k7 = st.columns(3)

# if pd.notna(latest_pnl_pct):
#     k5.metric(
#         "P/L totale",
#         fmt_eur(latest_pnl),
#         delta=fmt_pct(latest_pnl_pct),
#         delta_color="normal"
#     )
# else:
#     k5.metric(
#         "P/L totale",
#         fmt_eur(latest_pnl)
#     )

# if pd.notna(latest_daily_pl_pct):
#     k6.metric(
#         "P/L Giornaliero",
#         fmt_eur(latest_daily_pl),
#         delta=fmt_pct(latest_daily_pl_pct),
#         delta_color="normal"
#     )
# else:
#     k6.metric(
#         "P/L Giornaliero",
#         fmt_eur(latest_daily_pl)
#     )

# if pd.notna(latest_realized_pct):
#     k7.metric(
#         "P/L realizzato",
#         fmt_eur(latest_realized),
#         delta=fmt_pct(latest_realized_pct),
#         delta_color="normal"
#     )
# else:
#     k7.metric(
#         "P/L realizzato",
#         fmt_eur(latest_realized)
#     )

st.markdown("### 📊 KPI Portafoglio")

c1, c2, c3, c4 = st.columns(4)

with c1:
    render_value_card(latest_value)

with c2:
    render_unrealized_card(
        value=unrealized_pl,
        pct=unrealized_pctt,
        daily_value=latest_daily_pl,
        daily_pct=latest_daily_pl_pct
    )

with c3:
    render_realized_card(
        realized_total=latest_realized,
        dividends_total=latest_dividends
    )

with c4:
    render_total_pl_card(
        total_pl=latest_pnl,
        total_pct=latest_pnl_pct,
        annualized_pct=annualized_pct
    )


# Main chart
st.subheader("Andamento del portafoglio nel tempo")

fig = portfolio_chart(series, bench_norm=bench_norm, benchmark_name=benchmark)

st.plotly_chart(fig, use_container_width=True)

# Tabs
tab_pos, tab_exp, tab_ops, tab_dl = st.tabs(
    ["Posizioni", "Esposizione", "Operazioni", "Download"]
)

with tab_pos:
    st.subheader("Posizioni correnti")
    current_view = current.reset_index().rename(columns={"index": "PositionKey"})

    ordered_cols = [
        "Ticker", "Intermediario", "Nome", "Tipo", "Area", "Settore", "Emittente", "Valuta",
        "Quantita", "Prezzo Attuale", "Valore", "Dividendi Netti Incassati",
        "Costo Medio Stimato", "Costo Totale Stimato", "P/L", "P/L %",
        "P/L Netto Stimato", "P/L Giornaliero", "P/L Giornaliero %"
    ]
    ordered_cols = [c for c in ordered_cols if c in current_view.columns]

    st.dataframe(
        current_view[ordered_cols]
        .style
        .format({
            "Prezzo Attuale": "{:,.4f}",
            "Valore": "€ {:,.2f}",
            "Dividendi Netti Incassati": "€ {:,.2f}",
            "Costo Medio Stimato": "{:,.4f}",
            "Costo Totale Stimato": "€ {:,.2f}",
            "P/L": "€ {:,.2f}",
            "P/L %": "{:.2%}",
            "P/L Netto Stimato": "€ {:,.2f}",
            "P/L Giornaliero": "€ {:,.2f}",
            "P/L Giornaliero %": "{:.2%}",
        })
        .apply(style_pl_column, axis=0),
        use_container_width=True
    )

with tab_exp:
    st.subheader("Allocazione")
    
    # ✅ PIE (Ticker)
    fig = allocation_pie_chart(exposure, column="Ticker")
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    
    c1, c2 = st.columns(2)
    
    # ✅ BAR Area
    if "Area" in exposure.columns and exposure["Area"].astype(str).str.strip().any():
        fig_area = allocation_bar_chart(exposure, column="Area", title="Per area")
        if fig_area:
            c1.plotly_chart(fig_area, use_container_width=True)
    
    # ✅ BAR Tipo
    if "Tipo" in exposure.columns and exposure["Tipo"].astype(str).str.strip().any():
        fig_tipo = allocation_bar_chart(exposure, column="Tipo", title="Per tipo")
        if fig_tipo:
            c2.plotly_chart(fig_tipo, use_container_width=True)

with tab_ops:
    st.subheader("Operazioni")
    all_tickers = ["Tutti"] + sorted(ops_enriched["Ticker"].unique().tolist())
    selected_ticker = st.selectbox("Filtra per ticker", all_tickers)

    show_ops = (ops_enriched if selected_ticker == "Tutti" else ops_enriched[ops_enriched["Ticker"] == selected_ticker])
    st.dataframe(show_ops, use_container_width=True)

with tab_dl:
    st.subheader("Download risultati")

    ts_csv = (
        series.reset_index()
        .rename(columns={"index": "Data"})
        .to_csv(index=False)
        .encode("utf-8")
    )
    current_csv = (
        current.reset_index()
        .rename(columns={"index": "Ticker"})
        .to_csv(index=False)
        .encode("utf-8")
    )
    ops_csv = ops.to_csv(index=False).encode("utf-8")

    d1, d2, d3 = st.columns(3)
    d1.download_button(
        "Scarica serie storica CSV",
        ts_csv,
        file_name="serie_storica_portafoglio.csv",
        mime="text/csv"
    )
    d2.download_button(
        "Scarica posizioni correnti CSV",
        current_csv,
        file_name="posizioni_correnti.csv",
        mime="text/csv"
    )
    d3.download_button(
        "Scarica operazioni CSV",
        ops_csv,
        file_name="operazioni_portafoglio.csv",
        mime="text/csv"
    )

st.markdown("---")
footer_text = CONFIG.get(ENV, CONFIG["DEV"])["title"]
footer_icon = CONFIG.get(ENV, CONFIG["DEV"])["icon"]

st.markdown(
    f"<div style='text-align: center; color: gray;'>"
    f"{CONFIG[ENV]['icon']} {CONFIG[ENV]['title']}"
    f"</div>",
    unsafe_allow_html=True
)
st.caption("Aggiornamento in tempo reale dei prezzi")
