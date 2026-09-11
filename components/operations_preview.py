import streamlit as st
import pandas as pd
from utils.i18n import t
from utils.display import get_display_columns, get_format_dict


def highlight_sell_col(col):
    name = str(col.name).strip().lower()

    keywords = ["quant", "qty", "quantity"]

    if any(k in name for k in keywords):
        return [
            "color: #DC2626" if pd.notna(v) and v < 0 else ""
            for v in col
        ]

    return [""] * len(col)


def render_operations_preview(ops_enriched):

    with st.expander(t("operations_preview_title"), expanded=False):

        st.caption(t("operations_preview_subtitle"))

        show_full = st.checkbox(t("show_all_columns"), value=False)

        columns_map = get_display_columns()

        if show_full:
            df_base = ops_enriched.copy()

            if "Data" in df_base.columns:
                df_base["Data"] = pd.to_datetime(df_base["Data"], errors="coerce")

            df_display = df_base.rename(columns=columns_map)
            fmt_dict = get_format_dict(df_base, columns_map)

            styled = (
                df_display
                .style
                .format(fmt_dict)
                .apply(highlight_sell_col, axis=0)
            )

            # st.dataframe(styled, use_container_width=True)
            st.dataframe(styled, width="stretch")  

        else:
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

            cols = [c for c in cols if c in ops_enriched.columns]

            df_base = ops_enriched[cols].sort_values("Data", ascending=False)

            if "Data" in df_base.columns:
                df_base["Data"] = pd.to_datetime(df_base["Data"], errors="coerce")

            df_display = df_base.rename(columns=columns_map)
            fmt_dict = get_format_dict(df_base, columns_map)

            styled = (
                df_display
                .style
                .format(fmt_dict)
                .apply(highlight_sell_col, axis=0)
            )

            # st.dataframe(styled, use_container_width=True)
            st.dataframe(styled, width="stretch")
