import streamlit as st
import pandas as pd

from utils.display import get_display_columns, get_format_dict_positions
from utils.formatting import style_pl_column
from utils.i18n import t

def render_positions_table(current):

    columns_map = get_display_columns()

    # ✅ toggle multilingua
    compact_view = st.toggle(t("compact_view"), value=True)

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

def render_operations_table(ops_enriched):

    columns_map = get_display_columns()

    # =========================
    # ✅ FILTRO TICKER
    # =========================
    all_tickers = [t("all_option")] + sorted(ops_enriched["Ticker"].unique().tolist())

    selected_ticker = st.selectbox(
        t("filter_ticker"),
        all_tickers
    )

    if selected_ticker == t("all_option"):
        df_base = ops_enriched.copy()
    else:
        df_base = ops_enriched[ops_enriched["Ticker"] == selected_ticker]

    # =========================
    # ✅ NORMALIZZAZIONE
    # =========================
    if "Data" in df_base.columns:
        df_base["Data"] = pd.to_datetime(df_base["Data"], errors="coerce")

    # =========================
    # ✅ ORDINAMENTO
    # =========================
    if "Data" in df_base.columns:
        df_base = df_base.sort_values("Data", ascending=False)

    # =========================
    # ✅ DISPLAY
    # =========================
    df_display = df_base.rename(columns=columns_map)

    # ✅ usa formatter centralizzato
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
