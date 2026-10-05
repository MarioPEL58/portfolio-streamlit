import pandas as pd
import streamlit as st

from services.backtest import backtest_portfolio
from utils.i18n import t

# Adatta questo import al modulo in cui hai inserito backtest_chart()
from components.charts import backtest_chart


def render_backtest(
    # holdings,
    # ops_enriched,
    current,
    closes,
    bench_series=None,
    benchmark_name="",):
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
    ) =backtest_portfolio(
        current=current,
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
    
    # --------------------------------------------------------
    # Portafoglio semplice
    # --------------------------------------------------------
    
    if len(target_weights) <= 5:
    
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
    # --------------------------------------------------------
    # Portafoglio complesso
    # --------------------------------------------------------
    
    else:
    
        weights_df = (
            target_weights
            .rename("Peso")
            .sort_values(ascending=False)
            .reset_index()
        )
    
        weights_df.columns = [
            t("ticker_label"),
            t("backtest_weight"),
        ]
    
        st.dataframe(
            weights_df,
            hide_index=True,
            width="stretch",
            column_config={
                t("ticker_label"):
                    st.column_config.TextColumn(
                        t("ticker_label"),
                        width="medium",
                    ),
    
                t("backtest_weight"):
                    st.column_config.NumberColumn(
                        t("backtest_weight"),
                        format="percent",
                        width="small",
                    ),
            },
        )
        
    # ========================================================
    # DEBUG benchmark
    # ========================================================
    
    if bench_series is not None:
        st.write(
            "DEBUG benchmark:",
            benchmark_name,
            "| Prima data:",
            bench_series.first_valid_index(),
            "| Ultima data:",
            bench_series.last_valid_index(),
            "| Osservazioni:",
            bench_series.notna().sum(),
        )
    else:
        st.write(
            "DEBUG benchmark: bench_series è None"
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
