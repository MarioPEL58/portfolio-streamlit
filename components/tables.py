import streamlit as st
import pandas as pd

from utils.display import get_display_columns, get_format_dict_positions
from utils.formatting import style_pl_column
from utils.i18n import t

def render_positions_table(current):

    columns_map = get_display_columns()

    # =========================
    # ✅ BASE
    # =========================
    df_base = current.reset_index().rename(columns={"index": "PositionKey"})

    ordered_cols = [
        "Ticker", "Intermediario", "Nome", "Tipo", "Area", "Settore", "Emittente", "Valuta",
        "Quantita", "Prezzo Attuale", "Valore", "Dividendi Netti Incassati",
        "Costo Medio Stimato", "Costo Totale Stimato", "P/L", "P/L %",
        "P/L Netto Stimato", "P/L Giornaliero", "P/L Giornaliero %"
    ]

    ordered_cols = [c for c in ordered_cols if c in df_base.columns]

    df_base = df_base[ordered_cols]

    # =========================
    # ✅ DISPLAY
    # =========================
    df_display = df_base.rename(columns=columns_map)

    # =========================
    # ✅ FORMAT CENTRALIZZATO
    # =========================
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
