# components/monte_carlo_view.py

import numpy as np
import pandas as pd
from utils.i18n import t
import plotly.graph_objects as go
import streamlit as st

from services.monte_carlo import (
    prepare_portfolio_mc,
    prepare_portfolio_ticker_mc,
    prepare_external_ticker_mc,
    estimate_mc_parameters,
    run_monte_carlo,
)


# ============================================================
# Formattazione
# ============================================================

def _format_currency(value: float) -> str:
    if value is None or not np.isfinite(value):
        return "-"

    return f"€ {value:,.0f}".replace(",", ".")


def _format_pct(value: float) -> str:
    if value is None or not np.isfinite(value):
        return "-"

    return f"{value * 100:.2f}%"


def _format_date(value) -> str:
    if value is None or pd.isna(value):
        return "-"

    return pd.Timestamp(value).strftime("%d/%m/%Y")
    
def _historical_quality(observations: int) -> tuple[str, str]:

    if observations < 252:
        return (
            t("mc_quality_insufficient"),
            t("mc_quality_insufficient_message"),
        )

    elif observations < 756:
        return (
            t("mc_quality_limited"),
            t("mc_quality_limited_message"),
        )

    elif observations < 1260:
        return (
            t("mc_quality_fair"),
            t("mc_quality_fair_message"),
        )

    else:
        return (
            t("mc_quality_broad"),
            t("mc_quality_broad_message"),
        )
# ============================================================
# Fan chart
# ============================================================

def _build_fan_chart(
    percentile_paths: pd.DataFrame,
    initial_value: float,
) -> go.Figure:

    df = percentile_paths.copy()

    x = df.index.to_numpy()

    fig = go.Figure()

    # --------------------------------------------------------
    # Fascia P10 - P90
    # --------------------------------------------------------

    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["P90"],
            mode="lines",
            line=dict(width=0),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["P10"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(31, 119, 180, 0.12)",
            line=dict(width=0),
            name="P10 - P90",
            hoverinfo="skip",
        )
    )

    # --------------------------------------------------------
    # Fascia P25 - P75
    # --------------------------------------------------------

    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["P75"],
            mode="lines",
            line=dict(width=0),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["P25"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(31, 119, 180, 0.25)",
            line=dict(width=0),
            name="P25 - P75",
            hoverinfo="skip",
        )
    )
    
    # --------------------------------------------------------
    # Mediana + tooltip P25 / P50 / P75
    # --------------------------------------------------------
    
    customdata = np.column_stack([
        df["P25"],
        df["P75"],
    ])
    
    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["P50"],
            mode="lines",
            name="Mediana",
            line=dict(
                color="#1f77b4",
                width=3,
            ),
            customdata=customdata,
            hovertemplate=(
                "<b>Anno %{x:.1f}</b><br><br>"
                "P75 € %{customdata[1]:,.0f}<br>"
                "<b>P50 € %{y:,.0f}</b><br>"
                "P25 € %{customdata[0]:,.0f}"
                "<extra></extra>"
            ),
        )
    )
    # --------------------------------------------------------
    # Capitale iniziale
    # --------------------------------------------------------

    fig.add_hline(
        y=initial_value,
        line_dash="dot",
        line_color="gray",
        annotation_text="Capitale iniziale",
    )

    fig.update_layout(
        title="Evoluzione simulata del capitale",
        xaxis_title="Anni",
        yaxis_title="Valore",
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        margin=dict(
            l=20,
            r=20,
            t=80,
            b=20,
        ),
    )

    fig.update_yaxes(
        tickprefix="€ ",
        separatethousands=True,
    )

    return fig


# ============================================================
# Parametri storici
# ============================================================

def _show_historical_parameters(params: dict):

    st.markdown("#### Dati storici")

    observations = params["observations"]

    volatility_observations = params.get(
        "volatility_observations",
        observations,
    )

    quality, quality_message = _historical_quality(
        observations
    )

    # ========================================================
    # Prima riga: parametri principali
    # ========================================================

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Rendimento annualizzato",
        _format_pct(params["mu"]),
    )

    col2.metric(
        "Volatilità annualizzata",
        _format_pct(params["sigma"]),
    )

    col3.metric(
        "Qualità storico",
        quality,
    )

    # ========================================================
    # Seconda riga: numero osservazioni
    # Manteniamo la stessa griglia a 3 colonne
    # ========================================================

    col1, col2, col3  = st.columns(3)

    col1.metric(
        "Osservazioni storico",
        f'{observations:,}'.replace(",", "."),
    )

    col2.metric(
        "Osservazioni volatilità",
        f'{volatility_observations:,}'.replace(",", "."),
    )
    # col3 volutamente vuota
    
    # ========================================================
    # Periodo storico
    # ========================================================

    st.caption(
        f'Periodo storico: '
        f'{_format_date(params["start_date"])}'
        f' - '
        f'{_format_date(params["end_date"])}'
    )

    # ========================================================
    # Indicazione qualità storico
    # ========================================================

    if quality == "Insufficiente":
        st.error(quality_message)

    elif quality == "Limitato":
        st.warning(quality_message)

    elif quality == "Discreto":
        st.info(quality_message)

    else:
        st.caption(quality_message)
        
# ============================================================
# Risultati simulazione
# ============================================================

def _show_results(result: dict):

    st.markdown("---")
    st.subheader("Risultati")

    final = result["final_percentiles"]

    # --------------------------------------------------------
    # Percentili
    # --------------------------------------------------------

    st.markdown("#### Capitale finale")

    cols = st.columns(5)

    cols[0].metric(
        "P10",
        _format_currency(final["P10"]),
    )

    cols[1].metric(
        "P25",
        _format_currency(final["P25"]),
    )

    cols[2].metric(
        "Mediana",
        _format_currency(final["P50"]),
    )

    cols[3].metric(
        "P75",
        _format_currency(final["P75"]),
    )

    cols[4].metric(
        "P90",
        _format_currency(final["P90"]),
    )

    # --------------------------------------------------------
    # Indicatori
    # --------------------------------------------------------

    st.markdown("#### Indicatori")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Capitale iniziale",
        _format_currency(result["initial_value"]),
    )

    col2.metric(
        "Valore mediano",
        _format_currency(result["median_final_value"]),
    )

    col3.metric(
        "CAGR mediano",
        _format_pct(result["median_cagr"]),
    )

    col4.metric(
        "Probabilità di perdita",
        _format_pct(result["probability_loss"]),
    )

    # --------------------------------------------------------
    # Grafico
    # --------------------------------------------------------

    fig = _build_fan_chart(
        percentile_paths=result["percentile_paths"],
        initial_value=result["initial_value"],
    )

    st.plotly_chart(
        fig,
        width="stretch",
        key="monte_carlo_fan_chart",
    )


# ============================================================
# UI principale
# ============================================================
def render_monte_carlo(
    series: pd.DataFrame,
    current: pd.DataFrame,
    closes: pd.DataFrame,
    holdings: pd.DataFrame,
    price_quality: pd.DataFrame,
    ops_enriched: pd.DataFrame,
):
    """
    Visualizza il modulo Monte Carlo.

    Modalità disponibili:

    1. Intero portafoglio
    2. Ticker del portafoglio
    3. Ticker esterno
    """
    # ========================================================
    # CSS LOCALE MONTE CARLO
    # ========================================================  
    st.html("""
    <style>
    .st-key-monte_carlo_module [data-testid="stMetricValue"] {
        font-size: 1.75rem;
    }
    
    .st-key-monte_carlo_module [data-testid="stMetricLabel"] {
        font-size: 0.90rem;
    }
    </style>
    """)
    # ========================================================
    # CONTAINER PRINCIPALE
    #
    # Tutte le st.metric contenute qui dentro ricevono
    # lo stile compatto definito sopra.
    # ========================================================
    
    with st.container(key="monte_carlo_module"):
        st.header("🎲 Monte Carlo")
    
        st.caption(
            "Simulazione probabilistica basata sul rendimento "
            "atteso e sulla volatilità del sottostante."
        )
        
        # ========================================================
        # Modalità
        # ========================================================
    
        mode = st.radio(
            "Simula",
            [
                "Intero portafoglio",
                "Ticker del portafoglio",
                "Ticker esterno",
            ],
            horizontal=True,
            key="mc_mode",
        )
    
        initial_value = None
        returns = None
        volatility_returns = None
        source_name = None
    
        # ========================================================
        # 1. INTERO PORTAFOGLIO
        # ========================================================
    
        if mode == "Intero portafoglio":
    
            source_name = "Intero portafoglio"
    
            try:
    
                initial_value, returns, volatility_returns = (
                    prepare_portfolio_mc(
                        series=series,
                        holdings=holdings,
                        price_quality=price_quality,
                        ops_enriched=ops_enriched,
                    )
                )
    
                st.info(
                    f"Capitale attuale: "
                    f"{_format_currency(initial_value)}"
                )
    
            except ValueError as exc:
    
                st.warning(str(exc))
                return
    
        # ========================================================
        # 2. TICKER DEL PORTAFOGLIO
        # ========================================================
    
        elif mode == "Ticker del portafoglio":
    
            if current is None or current.empty:
    
                st.warning(
                    "Non sono presenti posizioni aperte "
                    "nel portafoglio."
                )
    
                return
    
            if "Ticker" not in current.columns:
    
                st.warning(
                    "La colonna Ticker non è disponibile."
                )
    
                return
    
            portfolio_tickers = sorted(
                current["Ticker"]
                .dropna()
                .astype(str)
                .unique()
            )
    
            if not portfolio_tickers:
    
                st.warning(
                    "Nessun ticker disponibile "
                    "nel portafoglio."
                )
    
                return
    
            selected_ticker = st.selectbox(
                "Ticker",
                portfolio_tickers,
                key="mc_portfolio_ticker",
            )
    
            source_name = selected_ticker
    
            try:
    
                initial_value, returns = (
                    prepare_portfolio_ticker_mc(
                        current=current,
                        closes=closes,
                        ticker=selected_ticker,
                    )
                )
    
                st.info(
                    f"Valore attuale posizione: "
                    f"{_format_currency(initial_value)}"
                )
    
            except ValueError as exc:
    
                st.warning(str(exc))
                return
    
        # ========================================================
        # 3. TICKER ESTERNO
        # ========================================================
    
        else:
    
            col1, col2 = st.columns(2)
    
            with col1:
    
                external_ticker = st.text_input(
                    "Ticker Yahoo Finance",
                    value="VWCE.DE",
                    key="mc_external_ticker",
                )
    
            with col2:
    
                external_capital = st.number_input(
                    "Capitale da simulare (€)",
                    min_value=100.0,
                    value=10_000.0,
                    step=1_000.0,
                    key="mc_external_capital",
                )
    
            external_ticker = external_ticker.strip().upper()
    
            if not external_ticker:
                st.info("Inserisci un ticker.")
                return
    
            source_name = external_ticker
    
            # ----------------------------------------------------
            # Download storico
            # ----------------------------------------------------
    
            try:
    
                with st.spinner(
                    f"Scaricamento storico {external_ticker}..."
                ):
    
                    initial_value, returns, _ = (
                        prepare_external_ticker_mc(
                            ticker=external_ticker,
                            initial_value=external_capital,
                            period="max",
                        )
                    )
    
            except Exception as exc:
    
                st.error(
                    f"Impossibile recuperare "
                    f"{external_ticker}: {exc}"
                )
    
                return
    
        # ========================================================
        # Stima parametri storici
        # ========================================================
    
        try:
    
            historical_params = estimate_mc_parameters(
                returns=returns,
                volatility_returns=volatility_returns,
            )
    
        except ValueError as exc:
    
            st.warning(str(exc))
            return
    
        _show_historical_parameters(
            historical_params
        )
    
        # ========================================================
        # Parametri simulazione
        # ========================================================
    
        st.markdown("---")
        st.subheader("Parametri simulazione")
    
        parameter_mode = st.radio(
            "Rendimento e volatilità",
            [
                "Storici",
                "Personalizzati",
            ],
            horizontal=True,
            key="mc_parameter_mode",
        )
    
        # --------------------------------------------------------
        # Parametri storici
        # --------------------------------------------------------
    
        if parameter_mode == "Storici":
    
            mu = historical_params["mu"]
            sigma = historical_params["sigma"]
    
            col1, col2 = st.columns(2)
    
            col1.metric(
                "Rendimento atteso utilizzato",
                _format_pct(mu),
            )
    
            col2.metric(
                "Volatilità utilizzata",
                _format_pct(sigma),
            )
    
        # --------------------------------------------------------
        # Parametri personalizzati
        # --------------------------------------------------------
    
        else:
    
            historical_mu_pct = (
                historical_params["mu"] * 100
            )
    
            historical_sigma_pct = (
                historical_params["sigma"] * 100
            )
    
            if not np.isfinite(historical_mu_pct):
                historical_mu_pct = 7.0
    
            if not np.isfinite(historical_sigma_pct):
                historical_sigma_pct = 15.0
    
            col1, col2 = st.columns(2)
    
            with col1:
    
                mu_pct = st.number_input(
                    "Rendimento atteso annuo (%)",
                    min_value=-50.0,
                    max_value=100.0,
                    value=float(
                        round(historical_mu_pct, 2)
                    ),
                    step=0.25,
                    key="mc_custom_mu",
                )
    
            with col2:
    
                sigma_pct = st.number_input(
                    "Volatilità annua (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(
                        round(historical_sigma_pct, 2)
                    ),
                    step=0.25,
                    key="mc_custom_sigma",
                )
    
            mu = mu_pct / 100.0
            sigma = sigma_pct / 100.0
    
        # ========================================================
        # Orizzonte / simulazioni
        # ========================================================
    
        col1, col2 = st.columns(2)
    
        with col1:
    
            years = st.select_slider(
                "Orizzonte temporale",
                options=[
                    1,
                    3,
                    5,
                    10,
                    15,
                    20,
                    25,
                    30,
                ],
                value=10,
                format_func=lambda x: f"{x} anni",
                key="mc_years",
            )
    
        with col2:
    
            n_simulations = st.selectbox(
                "Numero simulazioni",
                [
                    1_000,
                    5_000,
                    10_000,
                    25_000,
                    50_000,
                ],
                index=2,
                format_func=lambda x: (
                    f"{x:,}".replace(",", ".")
                ),
                key="mc_n_simulations",
            )
    
        # ========================================================
        # Riepilogo
        # ========================================================
    
        st.markdown("#### Riepilogo")
    
        col1, col2, col3, col4 = st.columns(4)
    
        col1.metric(
            "Analisi",
            source_name,
        )
    
        col2.metric(
            "Capitale",
            _format_currency(initial_value),
        )
    
        col3.metric(
            "Rendimento atteso",
            _format_pct(mu),
        )
    
        col4.metric(
            "Volatilità",
            _format_pct(sigma),
        )
    
        # ========================================================
        # Avvio Monte Carlo
        # ========================================================
    
        run = st.button(
            "Avvia simulazione",
            type="primary",
            width="stretch",
            key="mc_run",
        )
    
        if not run:
            return
    
        # ========================================================
        # Simulazione
        # ========================================================
    
        try:
    
            with st.spinner(
                f"Esecuzione di "
                f"{n_simulations:,} simulazioni..."
            ):
    
                result = run_monte_carlo(
                    initial_value=initial_value,
                    mu=mu,
                    sigma=sigma,
                    years=years,
                    n_simulations=n_simulations,
                )
    
        except Exception as exc:
    
            st.error(
                f"Errore durante la simulazione: {exc}"
            )
    
            return
    
        # ========================================================
        # Risultati
        # ========================================================
    
        _show_results(result)
    
        # ========================================================
        # Disclaimer
        # ========================================================
    
        st.caption(
            "La simulazione Monte Carlo rappresenta scenari "
            "probabilistici basati sui parametri selezionati. "
            "I risultati non costituiscono una previsione dei "
            "rendimenti futuri."
        )
