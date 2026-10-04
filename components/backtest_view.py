import streamlit as st

from services.backtest import backtest_initial_portfolio
from utils.i18n import t


def render_backtest(
    holdings,
    ops_enriched,
    closes,
):
    rebalance_frequency = st.selectbox(
        t("backtest_rebalance_frequency"),
        options=[
            "yearly",
            "semiannual",
            "quarterly",
            "monthly",
            "none",
        ],
    )

    backtest, target_weights, initial_value, initial_date = (
        backtest_initial_portfolio(
            holdings=holdings,
            ops_enriched=ops_enriched,
            closes=closes,
            rebalance_frequency=rebalance_frequency,
        )
    )

    # Per ora debug
    st.write(
        t("backtest_initial_date"),
        initial_date.strftime("%d/%m/%Y"),
    )

    st.write(
        t("backtest_initial_value"),
        f"€ {initial_value:,.2f}",
    )

    st.dataframe(
        target_weights.rename(
            t("backtest_weight")
        )
    )
    
    st.write("Pesi target:")
    st.dataframe(
        target_weights.rename("Peso")
    )
    
    st.write("Ribilanciamenti:")
    st.dataframe(
        backtest.loc[
            backtest["Ribilanciamento"],
            [
                "Valore portafoglio",
                "Data teorica ribilanciamento",
            ],
        ]
    )
    return backtest
