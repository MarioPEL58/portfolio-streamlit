import streamlit as st
import pandas as pd

from utils.display import get_display_columns, get_format_dict_positions
from utils.formatting import style_pl_column
from utils.i18n import t

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

    st.dataframe(styled, use_container_width=True)
    
def render_performance_table(current):

    columns_map = get_display_columns()

    cols = [
        "Ticker",
        "Nome",
        "Valore",
        "P/L Giornaliero",
        "P/L Giornaliero %",
        "P/L 7 Giorni",
        "P/L 7 Giorni %",
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
        use_container_width=True
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

    st.dataframe(styled, use_container_width=True)
