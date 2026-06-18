import os
import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.i18n import init_language, t
from components.sidebar import render_sidebar, resolve_file_source
from components.charts import portfolio_chart
from components.charts import allocation_pie_chart, allocation_bar_chart
from components.charts import daily_pl_bar_chart_by_sign, sharpe_gauge
from components.operations_preview import render_operations_preview
from components.filters import render_filters
from services.excel_loader import load_dividends_from_excel, load_operations_from_excel
from services.market_data import download_close_prices, download_last_intraday_timestamp
from services.portfolio import build_portfolio
from services.portfolio_metrics import compute_portfolio_xirr, compute_sharpe_ratio
from services.portfolio_metrics import compute_flow_adjusted_returns, compute_sharpe_from_returns
from services.market_status import compute_market_update_label
from services.benchmark import build_flow_adjusted_benchmark
from utils.formatting import fmt_eur, fmt_pct, style_pl_column
from utils.demo import create_demo_file
from utils.display import get_display_columns
from components.tables import render_positions_table, render_operations_table
from components.downloads import render_download_tab

from utils.kpi_cards import (
    render_value_card,
    render_unrealized_card,
    render_realized_card,
    render_total_pl_card
)

from config.config import load_config

CONFIG = load_config()

ENV = os.getenv("ENV", "DEV")

# 🔹 Config letta da TOML
env_cfg = CONFIG["env"][ENV]
ui_cfg = CONFIG["ui"]

# 🔹 Page config
st.set_page_config(
    page_title=env_cfg["title"],
    page_icon=env_cfg["icon"],
    layout="wide"
)

LANG = init_language(CONFIG)
# 🔹 Header
st.markdown(f"## {env_cfg['icon']} {env_cfg['title']}")
st.caption(t("subtitle"))

# ENV check 
if ENV == "DEV":
    st.warning(t("dev_warning"))

# Sidebar
sidebar_cfg = render_sidebar()
uploaded_file = sidebar_cfg["uploaded_file"]
benchmark = sidebar_cfg["benchmark"]
show_benchmark = sidebar_cfg["show_benchmark"]
min_filter_date = sidebar_cfg["min_filter_date"]

# Input source
if st.session_state.get("use_demo", False):
    file_source = create_demo_file(LANG)
    file_label = "Demo file"
    st.session_state.use_demo = False
else:
    file_source, file_label = resolve_file_source(uploaded_file)

if file_source is None:
    st.info(t("upload_prompt"))
    st.stop()

# Load data
try:
    ops = load_operations_from_excel(file_source)
    dividends = load_dividends_from_excel(file_source)

    ops["Data"] = pd.to_datetime(ops["Data"])

    data_min = ops["Data"].min()
    data_max = ops["Data"].max()

    six_months_ago = pd.Timestamp.today() - pd.DateOffset(months=6)

    if six_months_ago > data_max:
        default_start = data_min
    else:
        default_start = max(data_min, six_months_ago)

    default_start = default_start.date()

except Exception as e:
    st.error(f"{t('load_error')} {e}")
    st.stop()

effective_min_filter_date = min_filter_date or default_start

# ops = ops[ops["Data"] >= pd.Timestamp(effective_min_filter_date)]
if ops.empty:
    st.warning(t("no_ops_after_date"))
    st.stop()

st.success(f"{t('file_loaded')} {file_label}")

# =========================
# 🎛️ FILTER CONTEXT ✅
# =========================
filter_ctx = render_filters(ops, dividends)

ops_filtered = filter_ctx["ops"]
dividends_filtered = filter_ctx["dividends"]
filtered_tickers = filter_ctx["tickers"]

# Price download
start_date = ops["Data"].min().normalize()
end_date = pd.Timestamp.today().normalize()

closes, missing = download_close_prices(
    filtered_tickers,
    start_date,
    end_date
)

if closes.empty:
    st.error(t("no_prices"))
    st.stop()

if missing:
    st.warning(t("missing_tickers") + ", ".join(missing))

# Portfolio
series, current, holdings, exposure, ops_enriched = build_portfolio(ops_filtered, closes, dividends_filtered)

if series.empty:
    st.error(t("portfolio_error"))
    st.stop()

render_operations_preview(ops_enriched)
# with st.expander("Anteprima operazioni", expanded=False):
#    st.dataframe(ops_enriched, use_container_width=True)

# =========================
# KPIs
# =========================
latest_value = float(series["Valore portafoglio"].iloc[-1])
latest_invested = float(series["Capitale investito"].iloc[-1])
latest_pnl = float(series["P/L trading"].iloc[-1])
latest_daily_pl = float(series["P/L Giornaliero"].iloc[-1])
latest_daily_pl_pct = float(series["P/L Giornaliero %"].iloc[-1])

latest_realized = float(series["P/L realizzato"].iloc[-1])
latest_dividends = float(series["Dividendi netti"].sum())

# =========================
# XIRR + flussi
# =========================
xirr_value, xirr_flows = compute_portfolio_xirr(
    ops_enriched=ops_enriched,
    dividends=dividends_filtered,
    final_value=latest_value,
    valuation_date=series.index.max()
)
# =========================
# sharpe ratio
# =========================
#   not correct   sharpe = compute_sharpe_ratio(series["Valore portafoglio"])

flow_adjusted_returns = compute_flow_adjusted_returns(
    portfolio_value=series["Valore portafoglio"],
    flows_df=ops_enriched,
    flow_col="Operazioni"
)
sharpe = compute_sharpe_from_returns(flow_adjusted_returns)
# =========================
# Benchmark
# =========================
bench_norm = None

# =========================
# ✅ Benchmark flow-adjusted
# =========================
bench_series = None

if show_benchmark and benchmark.strip():
    bench_df, _ = download_close_prices(
        [benchmark.strip()],
        start_date,
        end_date
    )

    if not bench_df.empty and benchmark.strip() in bench_df.columns:
        b = bench_df[benchmark.strip()].dropna()
        
        #OLD investing all capital on the first day
        # if not b.empty and b.iloc[0] != 0:
        #     bench_norm = abs(series["Capitale investito"].iloc[-1]) * (b / b.iloc[0])

        if not b.empty:
        
            # ✅ prepara flows per benchmark
            flows_input = xirr_flows.copy()
            
            # ✅ RIMUOVE la riga finale sintetica
            if "Valore finale" in flows_input.columns:
                flows_input = flows_input[flows_input["Valore finale"].fillna(0) == 0]
                
            # ✅ Flow corretto (solo flussi di acquisto / vendita no Dividendi per correto confronto valore portfolio )
            flows_input["Flow"] = flows_input["Operazioni"].fillna(0.0)
        
            flows_input = flows_input[["Data", "Flow"]]
            #debug 
            # st.write(flows_input.head(10))
            # ✅ nuovo benchmark corretto
            bench_series = build_flow_adjusted_benchmark(
                flows_df=flows_input,
                benchmark_prices=b
            )

# =========================
# Breakdown P/L
# =========================
sell_ops = ops_enriched.loc[ops_enriched["Quantita"] < 0].copy()

realized_trading = (
    sell_ops["RealizedTradePL"].sum()
    if not sell_ops.empty else 0.0
)

realized_dividends = latest_dividends
realized_total = realized_trading + realized_dividends

# Non realizzato = somma P/L posizioni aperte
unrealized_pl = float(current["P/L"].sum()) if not current.empty else 0.0

open_cost = float(current["Costo Totale Stimato"].sum()) if not current.empty else 0.0
unrealized_pct = unrealized_pl / open_cost if open_cost != 0 else None

# Totale coerente con il breakdown
total_pl = realized_total + unrealized_pl
total_pct = total_pl / abs(latest_invested) if latest_invested != 0 else None

open_daily_pl = float(current["P/L Giornaliero"].sum()) if not current.empty else 0.0
open_value = float(current["Valore"].sum()) if not current.empty else 0.0
open_daily_pct = open_daily_pl / (open_value - open_daily_pl) if (open_value - open_daily_pl) != 0 else None

# =========================
# KPI cards
# =========================
st.markdown(f"### {t('kpi_title')}")

c1, c2, c3, c4 = st.columns(4)

with c1:
    render_value_card(latest_value, abs(latest_invested))
with c2:
    render_unrealized_card(
        value=unrealized_pl,
        pct=unrealized_pct,
        daily_value=open_daily_pl,
        daily_pct=open_daily_pct
    )
with c3:
    render_realized_card(
        realized_total=realized_total,
        dividends_total=realized_dividends
    )
with c4:
    render_total_pl_card(
        total_pl=total_pl,
        total_pct=total_pct,
        annualized_pct=xirr_value
    )

# ✅ timestamp intraday per il solo label
intraday_last_ts = download_last_intraday_timestamp(
    filtered_tickers
)

markets = []
if "Mercato" in ops_filtered.columns:
    markets = (
        ops_filtered["Mercato"]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )

update_label = compute_market_update_label(
    closes=closes,
    intraday_last_ts=intraday_last_ts,
    markets=markets,
    tz_name="Europe/Rome"
)

st.caption(update_label)

# Main chart

st.subheader(t("charts_title"))

tab_perf, tab_daily, tab_unrealized, tab_analysis = st.tabs([
    t("tab_perf"),
    t("tab_daily"),
    t("tab_unrealized"),
    t("tab_analysis")
])

with tab_perf:
    # fig = portfolio_chart(
    #     series,
    #     bench_norm=bench_norm,
    #     benchmark_name=benchmark
    # )
    
    min_date = min_filter_date or default_start
    
    filtered_series = series[
        series.index >= pd.Timestamp(min_date)
    ]
    # benchmark filtrato (vista) old bench_norm tutto invertito il primo giorno 
    # if bench_norm is not None:
    #     filtered_bench_norm = bench_norm[
    #         bench_norm.index >= pd.Timestamp(min_date)
    #     ]
    
    #     # allineamento (molto importante)
    #     filtered_bench_norm = filtered_bench_norm.reindex(filtered_series.index)
    #     filtered_bench_norm = filtered_bench_norm.ffill()
    # else:
    #     filtered_bench_norm = None
    #
    # fig = portfolio_chart(
    #     filtered_series,
    #     bench_norm=filtered_bench_norm,
    #     benchmark_name=benchmark
    # )
    if bench_series is not None:
        filtered_bench = bench_series[bench_series.index >= pd.Timestamp(min_date)]
    
        # ✅ allinea al portafoglio
        filtered_bench = filtered_bench.reindex(filtered_series.index)
        filtered_bench = filtered_bench.ffill()
    else:
        filtered_bench = None
    
    fig = portfolio_chart(
        filtered_series,
        bench_norm=filtered_bench,   # nome parametro puoi cambiarlo dopo
        benchmark_name=benchmark
    )

    st.plotly_chart(fig, use_container_width=True)

with tab_daily:
    st.subheader(t("daily_title"))
    view_mode = st.radio(
        t("view_mode"),
        options=[t("view_top"), t("view_all")],
        horizontal=True,
        key="view_mode_daily"
    )
    # copia df base
    df_view = current.copy()
    
    if view_mode == t("view_top"):
        # NON filtrare qui per segno — lo fa già la funzione
        top_n = 10
    else:
        top_n = None
        
    max_abs_pct = 0.01
    if current is not None and not current.empty and "P/L Giornaliero %" in current.columns:
        max_abs_pct = pd.to_numeric(
            current["P/L Giornaliero %"],
            errors="coerce"
        ).abs().max()

        if pd.isna(max_abs_pct) or max_abs_pct == 0:
            max_abs_pct = 0.01

    # ✅ Grafico posizioni in profitto
    st.markdown(t("profit_section"))

    fig_pos = daily_pl_bar_chart_by_sign(
        current=df_view,
        positive=True,
        label_col="Ticker",    
        pl_col="P/L Giornaliero",
        pl_pct_col="P/L Giornaliero %",
        max_abs_pct=max_abs_pct,
        top_n=top_n
    )

    if fig_pos:
        st.plotly_chart(fig_pos, use_container_width=True)
    else:
        st.caption(t("no_profit_today"))
        
    # ✅ Grafico posizioni in perdita
    st.markdown(t("loss_section"))

    fig_neg = daily_pl_bar_chart_by_sign(
        current=df_view,
        positive=False,
        label_col="Ticker",
        pl_col="P/L Giornaliero",
        pl_pct_col="P/L Giornaliero %",
        max_abs_pct=max_abs_pct,
        top_n=top_n
    )

    if fig_neg:
        st.plotly_chart(fig_neg, use_container_width=True)
    else:
        st.caption(t("no_loss_today"))
        
with tab_unrealized:
    st.subheader(t("unrealized_title"))

    view_mode = st.radio(
        t("view_mode"),
        options=[t("view_top"), t("view_all")],
        horizontal=True,
        key="view_mode_unrealized"
    )

    # copia df base
    df_view = current.copy()

    if view_mode == t("view_top"):
        top_n = 10
    else:
        top_n = None

    # ✅ calcolo max per scala %
    max_abs_pct = 0.01
    if current is not None and not current.empty and "P/L %" in current.columns:
        max_abs_pct = pd.to_numeric(
            current["P/L %"],
            errors="coerce"
        ).abs().max()

        if pd.isna(max_abs_pct) or max_abs_pct == 0:
            max_abs_pct = 0.01

    # ✅ Posizioni in profitto (open)
    st.markdown(t("profit_section"))

    fig_pos = daily_pl_bar_chart_by_sign(
        current=df_view,
        positive=True,
        label_col="Ticker",
        pl_col="P/L",
        pl_pct_col="P/L %",
        max_abs_pct=max_abs_pct,
        top_n=top_n
    )

    if fig_pos:
        st.plotly_chart(fig_pos, use_container_width=True)
    else:
        st.caption(t("no_profit_open"))

    # ✅ Posizioni in perdita (open)
    st.markdown(t("loss_section"))

    fig_neg = daily_pl_bar_chart_by_sign(
        current=df_view,
        positive=False,
        label_col="Ticker",
        pl_col="P/L",
        pl_pct_col="P/L %",
        max_abs_pct=max_abs_pct,
        top_n=top_n
    )

    if fig_neg:
        st.plotly_chart(fig_neg, use_container_width=True)
    else:
        st.caption(t("no_loss_open"))

with tab_analysis:
    st.subheader(t("analysis_title"))

    fig = sharpe_gauge(sharpe)

    if fig:
        st.plotly_chart(fig, use_container_width=True)

# Tabs
tab_pos, tab_exp, tab_flu, tab_ops, tab_dl = st.tabs(
    [t("tab_positions"), t("tab_exposure"), t("tab_flows"), t("tab_operations"), t("tab_download")]
)

with tab_pos:
    st.subheader(t("positions_title"))
    render_positions_table(current)
    
with tab_exp:
    st.subheader(t("allocation_title"))
    
    # ✅ PIE (Ticker)
    fig = allocation_pie_chart(exposure, column="Ticker")
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    
    c1, c2 = st.columns(2)
    
    # ✅ BAR Area
    if "Area" in exposure.columns and exposure["Area"].astype(str).str.strip().any():
        fig_area = allocation_bar_chart(exposure, column="Area", title=t("allocation_area"))
        if fig_area:
            c1.plotly_chart(fig_area, use_container_width=True)
    
    # ✅ BAR Tipo
    if "Tipo" in exposure.columns and exposure["Tipo"].astype(str).str.strip().any():
        fig_tipo = allocation_bar_chart(exposure, column="Tipo", title=t("allocation_type"))
        if fig_tipo:
            c2.plotly_chart(fig_tipo, use_container_width=True)

with tab_flu:
    st.subheader(t("flows_title"))
    st.caption(t("flows_subtitle"))
  
    columns_map = get_display_columns()
    
    df_display = xirr_flows.rename(columns=columns_map)
    
    fmt_dict = {}
    
    # ✅ DATA
    if "Data" in xirr_flows.columns:
        fmt_dict[columns_map["Data"]] = "{:%d/%m/%Y}"

    for col in xirr_flows.columns:
        if col in ["Operazioni", "Dividendi", "Valore finale", "Totale"]:
            fmt_dict[columns_map[col]] = "€ {:,.2f}"
    
    st.dataframe(
        df_display.style.format(fmt_dict),
        use_container_width=True
    )

with tab_ops:
    st.subheader(t("operations_title"))
    render_operations_table(ops_enriched)

with tab_dl:
    st.subheader(t("download_title"))
    render_download_tab(series, current, ops)

st.markdown("---")
# 🔹 recupero config
env_cfg = CONFIG["env"][ENV]
app_cfg = CONFIG["app"]

# 🔹 footer
st.markdown(
    f"""
    <div style='text-align: center; color: gray; font-size: 0.9em;'>
        {env_cfg['icon']} {env_cfg['title']} • v{app_cfg['version']}
    </div>
    """,
    unsafe_allow_html=True
)
st.caption(t("footer_note"))
