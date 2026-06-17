import streamlit as st
import pandas as pd
import io
from utils.i18n import t
from utils.display import get_display_columns


def dataframe_to_excel_bytes(df: pd.DataFrame):
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    buffer.seek(0)
    return buffer


def render_download_tab(series, current, ops):

    st.subheader(t("download_title"))

    columns_map = get_display_columns()

    # =========================
    # ✅ PREPARE DATA
    # =========================

    ts_df = (
        series.reset_index()
        .rename(columns={"index": "Data"})
    )

    current_df = (
        current.reset_index()
        .rename(columns={"index": "Ticker"})
    )

    ops_df = ops.copy()

    # ✅ versione tradotta (opzionale ma consigliata)
    ts_display = ts_df.rename(columns=columns_map)
    current_display = current_df.rename(columns=columns_map)
    ops_display = ops_df.rename(columns=columns_map)

    # =========================
    # ✅ CSV EXPORT
    # =========================

    ts_csv = ts_display.to_csv(index=False).encode("utf-8")
    current_csv = current_display.to_csv(index=False).encode("utf-8")
    ops_csv = ops_display.to_csv(index=False).encode("utf-8")

    # =========================
    # ✅ XLSX EXPORT
    # =========================

    ts_xlsx = dataframe_to_excel_bytes(ts_display)
    current_xlsx = dataframe_to_excel_bytes(current_display)
    ops_xlsx = dataframe_to_excel_bytes(ops_display)

    # =========================
    # ✅ UI
    # =========================

    c1, c2, c3 = st.columns(3)

    # ---- SERIE ----
    with c1:
        st.download_button(
            t("download_series"),
            ts_csv,
            file_name="portfolio_series.csv",
            mime="text/csv"
        )

        st.download_button(
            t("download_series_xlsx"),
            ts_xlsx,
            file_name="portfolio_series.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # ---- POSITIONS ----
    with c2:
        st.download_button(
            t("download_positions"),
            current_csv,
            file_name="positions.csv",
            mime="text/csv"
        )

        st.download_button(
            t("download_positions_xlsx"),
            current_xlsx,
            file_name="positions.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # ---- OPERATIONS ----
    with c3:
        st.download_button(
            t("download_operations"),
            ops_csv,
            file_name="operations.csv",
            mime="text/csv"
        )

        st.download_button(
            t("download_operations_xlsx"),
            ops_xlsx,
            file_name="operations.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
