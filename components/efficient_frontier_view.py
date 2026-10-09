from __future__ import annotations

import pandas as pd
import streamlit as st

from services.efficient_frontier import (
    calculate_efficient_frontier,
)
import plotly.graph_objects as go
from utils.formatting import color_pl
from utils.portfolio_utils import build_ticker_names
from utils.i18n import t


def render_efficient_frontier(
    current: pd.DataFrame,
    closes: pd.DataFrame,
    ops: pd.DataFrame,
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
        
    if "efficient_frontier_result" not in st.session_state:
        st.session_state["efficient_frontier_result"] = None
    
    # ========================================================
    # Ticker Name
    # ========================================================
    # ticker_names = (
    #     ops
    #     .dropna(subset=["Ticker"])
    #     .sort_values("Data")
    #     .groupby("Ticker")["Nome"]
    #     .last()
    #     .fillna("")
    #     .to_dict()
    # )

    ticker_names = build_ticker_names(ops)
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
    # Session state
    # ========================================================
    
    if "efficient_frontier_result" not in st.session_state:
        st.session_state["efficient_frontier_result"] = None
    
    if ("efficient_frontier_portfolio_signature"not in st.session_state):
        st.session_state["efficient_frontier_portfolio_signature"] = None
    
    if ("efficient_frontier_selected_id" not in st.session_state):
        st.session_state["efficient_frontier_selected_id"] = None
    # ========================================================
    # Firma portafoglio corrente
    # ========================================================
    
    portfolio_signature = tuple(
        sorted(
            (
                str(ticker),
                round(float(weight), 10),
            )
            for ticker, weight
            in current_weights.items()
        )
    )
    
    previous_signature = st.session_state[
        "efficient_frontier_portfolio_signature"
    ]
    
    if previous_signature != portfolio_signature:
    
        st.session_state["efficient_frontier_result"] = None
        
        st.session_state["efficient_frontier_selected_id"] = None
        
        st.session_state["efficient_frontier_portfolio_signature"] = portfolio_signature
        
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
    # if not run_simulation:
    #     return None
    
    # result = calculate_efficient_frontier(
    #     closes=closes,
    #     current_weights=current_weights,
    #     num_portfolios=num_portfolios,
    #     use_risk_free=use_risk_free,
    #     risk_free_rate=risk_free_rate,
    # )

    # ========================================================
    # Calcolo simulazione
    # ========================================================
    
    if run_simulation:
    
        result = calculate_efficient_frontier(
            closes=closes,
            current_weights=current_weights,
            num_portfolios=num_portfolios,
            use_risk_free=use_risk_free,
            risk_free_rate=risk_free_rate,
        )
    
        st.session_state[
            "efficient_frontier_result"
        ] = result
    
    
    # ========================================================
    # Recupero ultima simulazione
    # ========================================================
    
    result = st.session_state.get(
        "efficient_frontier_result"
    )
    
    # Prima simulazione non ancora eseguita
    if result is None and not run_simulation:
        st.info(
            t("efficient_frontier_ready")
        )
        return None
        
    # Simulazione eseguita, ma dati realmente insufficienti
    if result is None:
        st.warning(
            t("efficient_frontier_no_data")
        )
        return None
        
    assets = result["assets"] 
    # ========================================================
    # Grafico Frontiera Efficiente
    # ========================================================
    
    simulations = result["simulations"]
    
    fig = go.Figure()
    
    # --------------------------------------------------------
    # Portafogli simulati
    # --------------------------------------------------------
    
    fig.add_trace(
        go.Scattergl(
            x=simulations["Volatility"] * 100.0,
            y=simulations["Return"] * 100.0,
            mode="markers",
            name=t("efficient_frontier_random_portfolios"),
            marker=dict(
                size=5,
                color=simulations["Sharpe"],
                colorscale="Viridis",
                opacity=0.45,
                colorbar=dict(
                    title=t(
                        "efficient_frontier_sharpe"
                    )
                ),
            ),
            customdata=simulations[
                ["Sharpe"]
            ].to_numpy(),
            hovertemplate=(
                f"<b>{t('efficient_frontier_random_portfolio')}</b>"
                "<br>"
                f"{t('efficient_frontier_volatility')}: "
                "%{x:.2f}%"
                "<br>"
                f"{t('efficient_frontier_return')}: "
                "%{y:.2f}%"
                "<br>"
                f"{t('efficient_frontier_sharpe')}: "
                "%{customdata[0]:.2f}"
                "<extra></extra>"
            ),
        )
    )
    
    min_vol = result["min_volatility"]

    fig.add_trace(
        go.Scattergl(
            x=[
                min_vol["volatility"]
                * 100.0
            ],
            y=[
                min_vol["return"]
                * 100.0
            ],
            mode="markers",
            name=t(
                "efficient_frontier_min_volatility"
            ),
            marker=dict(
                size=15,
                color="#E53935",
                symbol="square",
                line=dict(
                    color="black",
                    width=1,
                ),
            ),
            customdata=[
                [min_vol["sharpe"]]
            ],
            hovertemplate=(
                f"<b>{t('efficient_frontier_min_volatility')}</b>"
                "<br>"
                f"{t('efficient_frontier_volatility')}: "
                "%{x:.2f}%"
                "<br>"
                f"{t('efficient_frontier_return')}: "
                "%{y:.2f}%"
                "<br>"
                f"{t('efficient_frontier_sharpe')}: "
                "%{customdata[0]:.2f}"
                "<extra></extra>"
            ),
        )
    )
    
    max_sharpe = result["max_sharpe"]

    fig.add_trace(
        go.Scattergl(
            x=[
                max_sharpe["volatility"]
                * 100.0
            ],
            y=[
                max_sharpe["return"]
                * 100.0
            ],
            mode="markers",
            name=t(
                "efficient_frontier_max_sharpe"
            ),
            marker=dict(
                size=16,
                color="#00C853",
                symbol="diamond",
                line=dict(
                    color="black",
                    width=1,
                ),
            ),
            customdata=[
                [max_sharpe["sharpe"]]
            ],
            hovertemplate=(
                f"<b>{t('efficient_frontier_max_sharpe')}</b>"
                "<br>"
                f"{t('efficient_frontier_volatility')}: "
                "%{x:.2f}%"
                "<br>"
                f"{t('efficient_frontier_return')}: "
                "%{y:.2f}%"
                "<br>"
                f"{t('efficient_frontier_sharpe')}: "
                "%{customdata[0]:.2f}"
                "<extra></extra>"
            ),
        )
    )
    current_result = result[
        "current_portfolio"
    ]
    
    fig.add_trace(
        go.Scattergl(
            x=[
                current_result["volatility"]
                * 100.0
            ],
            y=[
                current_result["return"]
                * 100.0
            ],
            mode="markers",
            name=t(
                "efficient_frontier_current_portfolio"
            ),
            marker=dict(
                size=18,
                color="#D500F9",
                symbol="x",
                line=dict(
                    width=2,
                ),
            ),
            customdata=[
                [current_result["sharpe"]]
            ],
            hovertemplate=(
                f"<b>{t('efficient_frontier_current_portfolio')}</b>"
                "<br>"
                f"{t('efficient_frontier_volatility')}: "
                "%{x:.2f}%"
                "<br>"
                f"{t('efficient_frontier_return')}: "
                "%{y:.2f}%"
                "<br>"
                f"{t('efficient_frontier_sharpe')}: "
                "%{customdata[0]:.2f}"
                "<extra></extra>"
            ),
        )
    )
    
    fig.update_layout(
        title=t(
            "efficient_frontier_chart_title"
        ),
        xaxis_title=t(
            "efficient_frontier_volatility"
        ),
        yaxis_title=t(
            "efficient_frontier_return"
        ),
        hovermode="closest",
        height=650,
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
            t=100,
            b=20,
        ),
    )
    
    fig.update_xaxes(
        ticksuffix="%"
    )
    
    fig.update_yaxes(
        ticksuffix="%"
    )
    
    # st.plotly_chart(
    #     fig,
    #     width="stretch",
    # )
    chart_event = st.plotly_chart(
        fig,
        width="stretch",
        key="efficient_frontier_chart",
        on_select="rerun",
        selection_mode="points",
    )
    
    # ========================================================
    # conrollo selezione ID
    # ========================================================
    selected_points = (
        chart_event["selection"]["points"]
    )
    
    if selected_points:
    
        point_index = (
            selected_points[0]["point_index"]
        )
    
        st.session_state[
            "efficient_frontier_selected_id"
        ] = point_index
    
    # ========================================================
    # conrollo pesi selected 
    # ========================================================
    selected_id = st.session_state.get(
        "efficient_frontier_selected_id"
    )
    
    if selected_id is not None:
    
        selected_weights = pd.Series(
            result["weights_matrix"][
                selected_id
            ],
            index=result["assets"],
        )

        # st.write(
        #     f"Selected portfolio ID: {point_index}"
        # )
        # st.write(
        #     f"Somma pesi: "
        #     f"{selected_weights.sum():.6f}"
        # )
    
    # ========================================================
    # Periodo utilizzato
    # ========================================================

    start_date = pd.to_datetime(
        result["start_date"]
    )

    end_date = pd.to_datetime(
        result["end_date"]
    )
    
    # ========================================================
    # Ticker che limita lo storico comune
    # ========================================================
    
    first_valid_dates = (
        closes[assets]
        .apply(lambda s: s.first_valid_index())
        .dropna()
    )
    
    limiting_tickers = (
        first_valid_dates[
            first_valid_dates == first_valid_dates.max()
        ]
        .index
        .tolist()
    )
    
    limiting_labels = [
        f"{ticker} - {ticker_names.get(ticker, '')}".rstrip(" -")
        for ticker in limiting_tickers
    ]
    
    limiting_text = ", ".join(
        limiting_labels
    )
    
    st.caption(
        f"{t('efficient_frontier_period')}: "
        f"{start_date:%d/%m/%Y} → "
        f"{end_date:%d/%m/%Y}"
    )
    
    if limiting_tickers:
    
        st.caption(
            f"{t('efficient_frontier_limiting_ticker')}: "
            f"{limiting_text}"
        )
        
    history_days = (end_date - start_date).days
    
    if history_days < 365:
    
        st.warning(t("efficient_frontier_short_history"))
        
    elif history_days < 365 * 3:

        st.warning(
            f"{t('efficient_frontier_history_short')} "
            f"{t('efficient_frontier_limiting_ticker')}: "
            f"{limiting_text}"
        )
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
    # Tabella allocazioni
    # ========================================================
    
    st.subheader(
        t("efficient_frontier_allocations")
    )
    
    current_weights = result[
        "current_portfolio"
    ]["weights"]
    
    min_vol_weights = result[
        "min_volatility"
    ]["weights"]
    
    max_sharpe_weights = result[
        "max_sharpe"
    ]["weights"]
    
    
    allocation_df = pd.DataFrame(
        {
            "Ticker": result["assets"],
    
            t("efficient_frontier_name"): [
                ticker_names.get(ticker, "")
                for ticker in result["assets"]
            ],
    
            t("efficient_frontier_current"):
                current_weights.reindex(
                    result["assets"]
                ).values,
    
            t("efficient_frontier_min_vol_short"):
                min_vol_weights.reindex(
                    result["assets"]
                ).values,
    
            t("efficient_frontier_max_sharpe_short"):
                max_sharpe_weights.reindex(
                    result["assets"]
                ).values,
        }
    )
    
    # Delta
    allocation_df[
        t("efficient_frontier_delta_min_vol")
    ] = (
        allocation_df[
            t("efficient_frontier_min_vol_short")
        ]
        - allocation_df[
            t("efficient_frontier_current")
        ]
    )
    
    allocation_df[
        t("efficient_frontier_delta_max_sharpe")
    ] = (
        allocation_df[
            t("efficient_frontier_max_sharpe_short")
        ]
        - allocation_df[
            t("efficient_frontier_current")
        ]
    )
    
    if selected_weights is not None:

        allocation_df[
            t("efficient_frontier_selected")
        ] = (
            selected_weights
            .reindex(result["assets"])
            .values
        )
    # Ordine finale colonne
    ordered_cols = [
            "Ticker",
            t("efficient_frontier_name"),
            t("efficient_frontier_current"),
            t("efficient_frontier_min_vol_short"),
            t("efficient_frontier_delta_min_vol"),
            t("efficient_frontier_max_sharpe_short"),
            t("efficient_frontier_delta_max_sharpe"),
    ]
    if selected_weights is not None:
    
        ordered_cols.append(
            t("efficient_frontier_selected")
        )
        
    allocation_df = allocation_df[
        ordered_cols
    ]
    
    percentage_columns = [
        t("efficient_frontier_current"),
        t("efficient_frontier_min_vol_short"),
        t("efficient_frontier_delta_min_vol"),
        t("efficient_frontier_max_sharpe_short"),
        t("efficient_frontier_delta_max_sharpe"),
    ]
    
    if selected_weights is not None:
        percentage_columns.append(
            t("efficient_frontier_selected")
        )
        
    allocation_df[
        percentage_columns
    ] *= 100.0
    
    allocation_df = (
        allocation_df
        .sort_values(
            t("efficient_frontier_current"),
            ascending=False,
        )
        .reset_index(drop=True)
    )
    
    delta_min_col = t(
        "efficient_frontier_delta_min_vol"
    )
    
    delta_sharpe_col = t(
        "efficient_frontier_delta_max_sharpe"
    )
    # degug 
    st.write(
        allocation_df.columns.tolist()
    )
    # end debug 
    styled_allocation_df = (
        allocation_df.style
        .map(
            color_pl,
            subset=[
                delta_min_col,
                delta_sharpe_col,
            ],
        )
    )
    
    st.dataframe(
        styled_allocation_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Ticker":
                st.column_config.TextColumn(
                    "Ticker"
                ),
    
            t("efficient_frontier_name"):
                st.column_config.TextColumn(
                    t("efficient_frontier_name")
                ),
    
            t("efficient_frontier_current"):
                st.column_config.NumberColumn(
                    t("efficient_frontier_current"),
                    format="%.2f%%",
                ),
    
            t("efficient_frontier_min_vol_short"):
                st.column_config.NumberColumn(
                    t("efficient_frontier_min_vol_short"),
                    format="%.2f%%",
                ),
    
            delta_min_col:
                st.column_config.NumberColumn(
                    delta_min_col,
                    format="%+.2f%%",
                ),
    
            t("efficient_frontier_max_sharpe_short"):
                st.column_config.NumberColumn(
                    t("efficient_frontier_max_sharpe_short"),
                    format="%.2f%%",
                ),
    
            delta_sharpe_col:
                st.column_config.NumberColumn(
                    delta_sharpe_col,
                    format="%+.2f%%",
                ),
            
            t("efficient_frontier_selected"):
                st.column_config.NumberColumn(
                    t("efficient_frontier_selected"),
                    format="%.2f%%",
                ),
        },
    )
    # ========================================================
    # Return
    # ========================================================

    return result
