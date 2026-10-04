import pandas as pd
import streamlit as st

from services.backtest import backtest_initial_portfolio
from utils.i18n import t

# Adatta questo import al modulo in cui hai inserito backtest_chart()
from components.charts import backtest_chart


def render_backtest(
    holdings,
    ops_enriched,
    closes,
    bench_series=None,
    benchmark_name="",
):
    # ========================================================
    # Frequenza ribilanciamento
    # ========================================================

    frequency_labels = {
        "monthly": t("backtest_frequency_monthly"),
        "quarterly": t("backtest_frequency_quarterly"),
        "semiannual": t("backtest_frequency_semiannual"),
        "yearly": t("backtest_frequency_yearly"),
        "none": t("backtest_frequency_none"),
    }

    rebalance_frequency = st.selectbox(
        t("backtest_rebalance_frequency"),
        options=list(frequency_labels.keys()),
        format_func=lambda value: frequency_labels[value],
        index=3,  # yearly
        key="backtest_rebalance_frequency",
    )

    # ========================================================
    # Calcolo backtest
    # ========================================================

    (
        backtest,
        target_weights,
        initial_value,
        initial_date,
    ) = backtest_initial_portfolio(
        holdings=holdings,
        ops_enriched=ops_enriched,
        closes=closes,
        rebalance_frequency=rebalance_frequency,
    )

    if backtest is None or backtest.empty:
        return None

    end_date = backtest.index.max()

    # ========================================================
    # Riepilogo
    # ========================================================

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            t("backtest_period"),
            (
                f"{initial_date:%d/%m/%Y}"
                f" → "
                f"{end_date:%d/%m/%Y}"
            ),
        )

    with col2:
        st.metric(
            t("backtest_initial_value"),
            f"€ {initial_value:,.2f}",
        )

    # ========================================================
    # Allocazione iniziale
    # ========================================================

    st.subheader(
        t("backtest_initial_allocation")
    )

    weight_columns = st.columns(
        len(target_weights)
    )

    for column, (ticker, weight) in zip(
        weight_columns,
        target_weights.items(),
    ):
        with column:
            st.metric(
                ticker,
                f"{weight:.2%}",
            )

    # ========================================================
    # Preparazione benchmark
    # ========================================================

    filtered_bench = None

    if bench_series is not None:

        filtered_bench = bench_series.copy()

        # -----------------------------------------------
        # Index Datetime
        # -----------------------------------------------

        if not isinstance(
            filtered_bench.index,
            pd.DatetimeIndex,
        ):
            filtered_bench.index = pd.to_datetime(
                filtered_bench.index,
                errors="coerce",
            )

        # Elimina eventuali date non valide
        filtered_bench = filtered_bench.loc[
            ~filtered_bench.index.isna()
        ]

        filtered_bench = (
            filtered_bench
            .sort_index()
        )

        # -----------------------------------------------
        # Solo periodo del backtest
        # -----------------------------------------------

        filtered_bench = filtered_bench.loc[
            filtered_bench.index >= initial_date
        ]

        # -----------------------------------------------
        # Allineamento benchmark alle date del backtest
        # -----------------------------------------------

        filtered_bench = filtered_bench.reindex(
            backtest.index
        )

        filtered_bench = (
            filtered_bench
            .ffill()
        )

    # ========================================================
    # Grafico Backtest vs Benchmark
    # ========================================================

    fig = backtest_chart(
        backtest=backtest,
        benchmark=filtered_bench,
        benchmark_name=benchmark_name,
    )

    if fig is not None:

        benchmark_key = (
            str(benchmark_name)
            .strip()
            .replace(" ", "_")
            .replace(".", "_")
        )

        chart_key = (
            f"backtest_chart_"
            f"{benchmark_key}_"
            f"{rebalance_frequency}"
        )

        st.plotly_chart(
            fig,
            width="stretch",
            theme=None,
            key=chart_key,
        )

    # ========================================================
    # Return
    # Lo teniamo utile per eventuali sviluppi successivi.
    # ========================================================

    return backtest
