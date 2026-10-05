import pandas as pd
import streamlit as st

from services.backtest import (backtest_portfolio, build_backtest_benchmark, calculate_backtest_metrics,)
from utils.i18n import t

# Adatta questo import al modulo in cui hai inserito backtest_chart()
from components.charts import backtest_chart


def render_backtest(
    current,
    closes,
    benchmark_prices=None,
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

    if backtest is None or backtest.empty:
        return None
    # ========================================================
    # Benchmark dedicato al backtest
    # ========================================================
    
    backtest_benchmark = None
    
    if benchmark_prices is not None:
    
        backtest_benchmark = build_backtest_benchmark(
            benchmark_prices=benchmark_prices,
            backtest_index=backtest.index,
            initial_value=initial_value,
        )
        
    metrics = calculate_backtest_metrics(
        backtest=backtest,
        benchmark=backtest_benchmark,
    )

    # ========================================================
    # Grafico Backtest vs Benchmark
    # ========================================================

    fig = backtest_chart(
        backtest=backtest,
        benchmark=backtest_benchmark,
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
    # Metriche Backtest vs Benchmark
    # ========================================================
    
    if metrics is not None:
    
        st.subheader(
            t("backtest_metrics_title")
        )
    
        # ----------------------------------------------------
        # Portafoglio
        # ----------------------------------------------------
    
        st.caption(
            t("backtest_portfolio")
        )
    
        p1, p2, p3, p4 = st.columns(4)
    
        p1.metric(
            t("backtest_total_return"),
            f"{metrics['portfolio_total_return']:.2%}",
            delta=(
                f"{metrics['portfolio_total_return'] - metrics['benchmark_total_return']:+.2%}"
                if pd.notna(metrics["benchmark_total_return"])
                else None
            ),
        )
    
        p2.metric(
            t("backtest_cagr"),
            f"{metrics['portfolio_cagr']:.2%}",
            delta=(
                f"{metrics['portfolio_cagr'] - metrics['benchmark_cagr']:+.2%}"
                if pd.notna(metrics["benchmark_cagr"])
                else None
            ),
        )
    
        p3.metric(
            t("backtest_volatility"),
            f"{metrics['portfolio_volatility']:.2%}",
        )
    
        p4.metric(
            t("backtest_max_drawdown"),
            f"{metrics['portfolio_max_drawdown']:.2%}",
        )
    
        # ----------------------------------------------------
        # Benchmark
        # ----------------------------------------------------
    
        if (
            backtest_benchmark is not None
            and pd.notna(
                metrics["benchmark_total_return"]
            )
        ):
    
            st.caption(
                f"{t('backtest_benchmark')}: "
                f"{benchmark_name}"
            )
    
            b1, b2, b3, b4 = st.columns(4)
    
            b1.metric(
                t("backtest_benchmark_total_return"),
                f"{metrics['benchmark_total_return']:.2%}",
            )
    
            b2.metric(
                t("backtest_benchmark_cagr"),
                f"{metrics['benchmark_cagr']:.2%}",
            )
    
            b3.metric(
                t("backtest_benchmark_volatility"),
                f"{metrics['benchmark_volatility']:.2%}",
            )
    
            b4.metric(
                t("backtest_benchmark_max_drawdown"),
                f"{metrics['benchmark_max_drawdown']:.2%}",
            )
    
            # ------------------------------------------------
            # Metriche relative
            # ------------------------------------------------
    
            r1, r2, r3 = st.columns(3)
    
            r1.metric(
                t("backtest_active_return"),
                (
                    f"{metrics['active_return']:.2%}"
                    if pd.notna(
                        metrics["active_return"]
                    )
                    else "—"
                ),
            )
    
            r2.metric(
                t("backtest_tracking_error"),
                (
                    f"{metrics['tracking_error']:.2%}"
                    if pd.notna(
                        metrics["tracking_error"]
                    )
                    else "—"
                ),
            )
    
            r3.metric(
                t("backtest_information_ratio"),
                (
                    f"{metrics['information_ratio']:.2f}"
                    if pd.notna(
                        metrics["information_ratio"]
                    )
                    else "—"
                ),
            )
    # ========================================================
    # Return
    # Lo teniamo utile per eventuali sviluppi successivi.
    # ========================================================

    return backtest
