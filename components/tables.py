import streamlit as st
import pandas as pd

from utils.display import get_display_columns, get_format_dict_positions
from utils.formatting import style_pl_column
from utils.i18n import t
from services.portfolio_metrics import compute_var_historical

def render_positions_table(current):

    columns_map = get_display_columns()
    
    # =========================
    # ✅ HEADER CONTROL BAR
    # =========================
    c1, c2 = st.columns([1, 3])

    with c1:
        compact_view = st.toggle(
            t("compact_view"),
            value=True,
            help=t("compact_view_help")
        )

    with c2:
        st.caption(f"📦 {len(current)} {t('positions_count')}")

    st.divider()

    df_base = current.reset_index().rename(columns={"index": "PositionKey"})

    # =========================
    # ✅ SCELTA COLONNE
    # =========================
    if compact_view:
        cols = [
            "Ticker",
            "Nome",
            "Quantita",
            "Prezzo Attuale",
            "Costo Medio Stimato",
            "Valore",
            "P/L",
            "P/L %",
            "P/L Giornaliero",
            "P/L Giornaliero %",
        ]
    else:
        cols = [
            "Ticker", "Intermediario", "Nome", "Tipo", "Area", "Settore", "Emittente", "Valuta",
            "Quantita", "Prezzo Attuale", "Valore", "Dividendi Netti Incassati",
            "Costo Medio Stimato", "Costo Totale Stimato", "P/L", "P/L %",
            "P/L Netto Stimato", "P/L Giornaliero", "P/L Giornaliero %",
        ]

    cols = [c for c in cols if c in df_base.columns]

    df_base = df_base[cols]

    # =========================
    # ✅ DISPLAY
    # =========================
    df_display = df_base.rename(columns=columns_map)

    fmt_dict = get_format_dict_positions(df_base, columns_map)

    # =========================
    # ✅ STYLING
    # =========================
    styled = (
        df_display
        .style
        .format(fmt_dict)
        .apply(style_pl_column, axis=0)
    )

    # st.dataframe(styled, use_container_width=True)    
    st.dataframe(styled, width="stretch")
    
def render_performance_table(current):

    columns_map = get_display_columns()

    cols = [
        "Ticker",
        "Nome",
        "P/L Giornaliero",
        "P/L Giornaliero %",
        "P/L 7 Giorni",
        "P/L 7 Giorni %",
        "P/L 30 Giorni",
        "P/L 30 Giorni %",
    ]

    cols = [c for c in cols if c in current.columns]

    df_base = current[cols].copy()

    if "P/L 7 Giorni" in df_base.columns:
        df_base = df_base.sort_values(
            "P/L 7 Giorni",
            ascending=False
        )

    # stesso approccio di render_positions_table
    df_display = df_base.rename(columns=columns_map)

    fmt_dict = get_format_dict_positions(
        df_base,
        columns_map
    )

    styled = (
        df_display
        .style
        .format(fmt_dict)
        .apply(style_pl_column, axis=0)
    )

    st.dataframe(
        styled,
        # use_container_width=True
        width="stretch"
    )
    
def render_operations_table(ops_enriched):

    columns_map = get_display_columns()

    # ✅ toggle compatto
    compact_view = st.toggle(t("compact_view"), value=True, key="compact_view_ops")

    # ✅ filtro ticker
    all_tickers = [t("all_option")] + sorted(ops_enriched["Ticker"].unique().tolist())

    selected_ticker = st.selectbox(
        t("filter_ticker"),
        all_tickers,
        key="operations_table_ticker"
    )

    if selected_ticker == t("all_option"):
        df_base = ops_enriched.copy()
    else:
        df_base = ops_enriched[ops_enriched["Ticker"] == selected_ticker].copy()

    # ✅ vista compatta / completa
    if compact_view:
        cols = [
            "Data",
            "Ticker",
            "Intermediario",
            "Tipo",
            "Quantita",
            "Prezzo",
            "AvgCostBefore",
            "RealizedTradePL",
        ]
    else:
        cols = list(df_base.columns)

    cols = [c for c in cols if c in df_base.columns]
    df_base = df_base[cols]

    # ✅ datetime
    if "Data" in df_base.columns:
        df_base["Data"] = pd.to_datetime(df_base["Data"], errors="coerce")

    # ✅ ordinamento
    if "Data" in df_base.columns:
        df_base = df_base.sort_values("Data", ascending=False)

    # ✅ traduzione colonne
    df_display = df_base.rename(columns=columns_map)

    # ✅ format centralizzato
    fmt_dict = get_format_dict_positions(df_base, columns_map)

    # ✅ highlight quantità negative
    def highlight_sell_col(col):
        name = str(col.name).strip().lower()
        if any(k in name for k in ["quant", "qty", "quantity"]):
            return [
                "color: #DC2626" if pd.notna(v) and v < 0 else ""
                for v in col
            ]
        return [""] * len(col)

    styled = (
        df_display
        .style
        .format(fmt_dict)
        .apply(highlight_sell_col, axis=0)
        .apply(style_pl_column, axis=0)
    )

    st.dataframe(styled, width="stretch")
    
def render_best_worst_days(flow_adjusted_returns, n_days=10):

    returns = flow_adjusted_returns.dropna().sort_index()

    if returns.empty:
        return

    # VaR 95% sulla serie completa
    var_giornaliero = compute_var_historical(returns, 0.95)

    with st.expander(t("tail_risk_best_worst_days")):

        # --------------------------
        # Selezione periodo
        # --------------------------
        period = st.segmented_control(
            t("tail_risk_period"),
            options=["1Y", "3Y", "5Y", "ALL"],
            default="1Y",
            key="tail_risk_period_selector"
        )

        end_date = returns.index.max()

        if period == "1Y":
            start_date = end_date - pd.DateOffset(years=1)

        elif period == "3Y":
            start_date = end_date - pd.DateOffset(years=3)

        elif period == "5Y":
            start_date = end_date - pd.DateOffset(years=5)

        else:
            start_date = returns.index.min()

        returns_period = returns.loc[start_date:end_date]

        # --------------------------
        # Migliori / peggiori giorni
        # --------------------------
        worst_days = returns_period.nsmallest(n_days)
        best_days = returns_period.nlargest(n_days)

        col_worst, col_best = st.columns(2)

        # ==========================
        # PEGGIORI
        # ==========================
        with col_worst:

            st.markdown(
                f"#### 📉 {t('tail_risk_worst_days_title')}"
            )

            worst_df = (
                worst_days
                .rename(t("tail_risk_return"))
                .to_frame()
            )

            worst_df.index.name = t("tail_risk_date")

            return_col = t("tail_risk_return")

            # Evidenzia i giorni oltre il VaR
            def highlight_var(value):
                if value <= -var_giornaliero:
                    return (
                        "background-color: rgba(231, 76, 60, 0.25); "
                        "color: #ff6b6b; "
                        "font-weight: bold;"
                    )
                return ""

            styled_worst = (
                worst_df.style
                .format({
                    return_col: "{:.2%}"
                })
                .map(
                    highlight_var,
                    subset=[return_col]
                )
            )

            st.dataframe(
                styled_worst,
                width="stretch"
            )

        # ==========================
        # MIGLIORI
        # ==========================
        with col_best:

            st.markdown(
                f"#### 📈 {t('tail_risk_best_days_title')}"
            )

            best_df = (
                best_days
                .rename(t("tail_risk_return"))
                .to_frame()
            )

            best_df.index.name = t("tail_risk_date")

            styled_best = (
                best_df.style
                .format({
                    return_col: "{:.2%}"
                })
            )

            st.dataframe(
                styled_best,
                width="stretch"
            )

        # --------------------------
        # Legenda
        # --------------------------
        st.caption(
            f"🔴 {t('tail_risk_var_highlight')} "
            f"({-var_giornaliero:.2%})"
        )
