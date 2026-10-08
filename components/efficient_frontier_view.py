from __future__ import annotations

import pandas as pd
import streamlit as st

from services.efficient_frontier import (
    calculate_efficient_frontier,
)

from utils.i18n import t


def render_efficient_frontier(
    current: pd.DataFrame,
    closes: pd.DataFrame,
    use_risk_free: bool = False,
    risk_free_rate: float = 0.0,
):
    # ========================================================
    # Controlli iniziali
    # ========================================================

    if current is None or current.empty:
        return None

    if closes is None or closes.empty:
        return None

    # ========================================================
    # Portafoglio corrente
    # ========================================================

    current_positive = current[
        current["Valore"] > 0
    ].copy()

    if current_positive.empty:
        return None

    current_values = (
        current_positive
        .groupby("Ticker")["Valore"]
        .sum()
    )

    current_total = float(
        current_values.sum()
    )

    if current_total <= 0:
        return None

    current_weights = (
        current_values
        / current_total
    )
    
    # ========================================================
    # Parametri simulazione
    # ========================================================
    with st.form(
        key="efficient_frontier_form",
    ):
        num_portfolios = st.select_slider(
            t("efficient_frontier_num_portfolios"),
            options=[
                10_000,
                25_000,
                50_000,
                75_000,
                100_000,
            ],
            value=50_000,
            format_func=lambda x: f"{x:,}",
            key="efficient_frontier_num_portfolios",
        )
        
        run_simulation = st.form_submit_button(
            t("efficient_frontier_run"),
            type="primary",
            icon=":material/play_arrow:",
            width="stretch",
        )
    # ========================================================
    # Calcolo Frontiera Efficiente
    # ========================================================
    if not run_simulation:
        return None
    
    result = calculate_efficient_frontier(
        closes=closes,
        current_weights=current_weights,
        num_portfolios=num_portfolios,
        use_risk_free=use_risk_free,
        risk_free_rate=risk_free_rate,
    )

    if result is None:
        st.warning(
            t("efficient_frontier_no_data")
        )
        return None

    # ========================================================
    # Periodo utilizzato
    # ========================================================

    start_date = pd.to_datetime(
        result["start_date"]
    )

    end_date = pd.to_datetime(
        result["end_date"]
    )

    st.caption(
        f"{t('efficient_frontier_period')}: "
        f"{start_date:%d/%m/%Y} → "
        f"{end_date:%d/%m/%Y}"
    )
    history_days = (end_date - start_date).days
    
    if history_days < 365:
    
        st.warning(t("efficient_frontier_short_history"))
        
    # ========================================================
    # Informazioni simulazione
    # ========================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            t("efficient_frontier_assets"),
            len(result["assets"]),
        )

    with col2:

        st.metric(
            t("efficient_frontier_simulations"),
            f"{result['num_portfolios']:,}",
        )

    with col3:

        if result["use_risk_free"]:

            st.metric(
                t("efficient_frontier_risk_free"),
                f"{result['risk_free_rate']:.2%}",
            )

        else:

            st.metric(
                t("efficient_frontier_risk_free"),
                t("efficient_frontier_risk_free_disabled"),
            )

    # ========================================================
    # Portafoglio corrente
    # ========================================================

    st.subheader(
        t("efficient_frontier_current_portfolio")
    )

    current_result = result[
        "current_portfolio"
    ]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        t("efficient_frontier_return"),
        f"{current_result['return']:.2%}",
    )

    c2.metric(
        t("efficient_frontier_volatility"),
        f"{current_result['volatility']:.2%}",
    )

    c3.metric(
        t("efficient_frontier_sharpe"),
        f"{current_result['sharpe']:.2f}",
    )

    # ========================================================
    # Portafoglio Min Volatility
    # ========================================================

    st.subheader(
        t("efficient_frontier_min_volatility")
    )

    min_vol = result[
        "min_volatility"
    ]

    m1, m2, m3 = st.columns(3)

    m1.metric(
        t("efficient_frontier_return"),
        f"{min_vol['return']:.2%}",
    )

    m2.metric(
        t("efficient_frontier_volatility"),
        f"{min_vol['volatility']:.2%}",
    )

    m3.metric(
        t("efficient_frontier_sharpe"),
        f"{min_vol['sharpe']:.2f}",
    )

    # ========================================================
    # Portafoglio Max Sharpe
    # ========================================================

    st.subheader(
        t("efficient_frontier_max_sharpe")
    )

    max_sharpe = result[
        "max_sharpe"
    ]

    s1, s2, s3 = st.columns(3)

    s1.metric(
        t("efficient_frontier_return"),
        f"{max_sharpe['return']:.2%}",
    )

    s2.metric(
        t("efficient_frontier_volatility"),
        f"{max_sharpe['volatility']:.2%}",
    )

    s3.metric(
        t("efficient_frontier_sharpe"),
        f"{max_sharpe['sharpe']:.2f}",
    )

    # ========================================================
    # Return
    # ========================================================

    return result
