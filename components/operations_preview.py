import streamlit as st
import pandas as pd
from utils.i18n import t
from utils.display import get_display_columns


# ✅ funzione RIUSABILE
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

        # =========================
        # ✅ SHOW ALL
        # =========================
        if show_full:
        
            df_base = ops_enriched.copy()
            df_display = df_base.rename(columns=columns_map)
            
            # st.write(df_base.dtypes)
            
            # ✅ FORMATI dinamici (robusti)
            fmt_dict = {}
        
            for col in df_base.columns:
        
                col_lower = col.lower()
        
                # ✅ DATA (PRIMA di tutto)
                if col_lower == "data":
                    fmt_dict[columns_map.get(col, col)] = "{:%d/%m/%Y}"

                # prezzi / costi
                if any(k in col_lower for k in ["prezzo", "cost", "price"]):
                    fmt_dict[columns_map.get(col, col)] = "{:,.2f}"
        
                # percentuali
                elif "%" in col:
                    fmt_dict[columns_map.get(col, col)] = "{:.2%}"
        
                # P/L o valori monetari
                elif any(k in col_lower for k in ["pl", "flow", "tax", "div"]):
                    fmt_dict[columns_map.get(col, col)] = "€ {:,.2f}"
        
            styled = (
                df_display
                .style
                .format(fmt_dict)
                .apply(highlight_sell_col, axis=0)
            )
        
            st.dataframe(styled, use_container_width=True)
        # =========================
        # ✅ PREVIEW
        # =========================
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

            df_base = (
                ops_enriched[cols]
                .sort_values("Data", ascending=False)
            )

            df_display = df_base.rename(columns=columns_map)

            # ✅ format sicuro
            fmt_dict = {}

            # ✅ DATA
            if "Data" in df_base.columns:
                fmt_dict[columns_map["Data"]] = "{:%d/%m/%Y}"
                
            if "Quantita" in df_base.columns:
                fmt_dict[columns_map["Quantita"]] = "{:,.2f}"
                
            if "Prezzo" in df_base.columns:
                fmt_dict[columns_map["Prezzo"]] = "{:,.2f}"

            if "AvgCostBefore" in df_base.columns:
                fmt_dict[columns_map["AvgCostBefore"]] = "{:,.2f}"

            if "RealizedTradePL" in df_base.columns:
                fmt_dict[columns_map["RealizedTradePL"]] = "€ {:,.2f}"

            styled = (
                df_display
                .style
                .format(fmt_dict)
                .apply(highlight_sell_col, axis=0)
            )

            st.dataframe(styled, use_container_width=True)
