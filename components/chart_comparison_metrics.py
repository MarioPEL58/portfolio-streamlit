import streamlit as st

from utils.i18n import t
from services.portfolio_metrics import compute_chart_comparison_metrics


def render_chart_comparison_metrics(
    portfolio_returns,
    benchmark_returns,
    benchmark_name,
    start_date,
):
    """
    Visualizza le metriche di confronto tra portafoglio
    e benchmark per il periodo selezionato nel grafico.
    """

    metrics = compute_chart_comparison_metrics(
        portfolio_returns=portfolio_returns,
        benchmark_returns=benchmark_returns,
        start_date=start_date,
    )

    with st.expander(
        t("chart_metrics_show"),
        expanded=False,
    ):

        # ====================================================
        # Periodo
        # ====================================================

        period_start = metrics["period_start"]
        period_end = metrics["period_end"]

        if period_start is not None and period_end is not None:
            st.caption(
                f"{t('chart_metrics_period')}: "
                f"{period_start.strftime('%d/%m/%Y')} → "
                f"{period_end.strftime('%d/%m/%Y')}"
            )

        # ====================================================
        # Performance
        # ====================================================

        portfolio_return = metrics["portfolio_return"]
        benchmark_return = metrics["benchmark_return"]
        outperformance = metrics["outperformance"]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            t("chart_metrics_portfolio"),
            (
                f"{portfolio_return:+.2%}"
                if portfolio_return is not None
                else "-"
            ),
        )

        col2.metric(
            f"{t('chart_metrics_benchmark')} {benchmark_name}",
            (
                f"{benchmark_return:+.2%}"
                if benchmark_return is not None
                else "-"
            ),
        )

        col3.metric(
            t("chart_metrics_outperformance"),
            (
                f"{outperformance * 100:+.2f} p.p."
                if outperformance is not None
                else "-"
            ),
        )

        # ====================================================
        # Rischio
        # ====================================================

        portfolio_volatility = metrics["portfolio_volatility"]
        benchmark_volatility = metrics["benchmark_volatility"]

        portfolio_max_drawdown = metrics[
            "portfolio_max_drawdown"
        ]

        benchmark_max_drawdown = metrics[
            "benchmark_max_drawdown"
        ]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            t("chart_metrics_portfolio_volatility"),
            (
                f"{portfolio_volatility:.2%}"
                if portfolio_volatility is not None
                else "-"
            ),
        )

        col2.metric(
            t("chart_metrics_benchmark_volatility"),
            (
                f"{benchmark_volatility:.2%}"
                if benchmark_volatility is not None
                else "-"
            ),
        )

        col3.metric(
            t("chart_metrics_portfolio_drawdown"),
            (
                f"{portfolio_max_drawdown:.2%}"
                if portfolio_max_drawdown is not None
                else "-"
            ),
        )

        col4.metric(
            t("chart_metrics_benchmark_drawdown"),
            (
                f"{benchmark_max_drawdown:.2%}"
                if benchmark_max_drawdown is not None
                else "-"
            ),
        )
        
        # ====================================================
        # Confronto relativo
        # ====================================================

        tracking_error = metrics["tracking_error"]
        information_ratio = metrics["information_ratio"]

        col1, col2 = st.columns(2)

        col1.metric(
            t("chart_metrics_tracking_error"),
            (
                f"{tracking_error:.2%}"
                if tracking_error is not None
                else "-"
            ),
        )

        col2.metric(
            t("chart_metrics_information_ratio"),
            (
                f"{information_ratio:.2f}"
                if information_ratio is not None
                else "-"
            ),
        )
