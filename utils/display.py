import pandas as pd
import streamlit as st
from utils.i18n import t


def get_display_columns():
    return {
        "Data": t("col_date"),
        "Ticker": t("col_ticker"),
        "Intermediario": t("col_broker"),
        "Nome": t("col_name"),
        "Tipo": t("col_type"),
        "Area": t("col_area"),
        "Settore": t("col_sector"),
        "Emittente": t("col_issuer"),
        "Valuta": t("col_currency"),
        "Quantita": t("col_quantity"),
        "Prezzo": t("col_trade_price"),
        "Prezzo Attuale": t("col_price_current"),
        "Valore": t("col_value"),
        "Dividendi Netti Incassati": t("col_dividends"),
        "Costo Medio Stimato": t("col_avg_cost"),
        "Costo Totale Stimato": t("col_total_cost"),
        "P/L": t("col_pl"),
        "P/L %": t("col_pl_pct"),
        "P/L Netto Stimato": t("col_pl_net"),
        "P/L Giornaliero": t("col_pl_daily"),
        "P/L Giornaliero %": t("col_pl_daily_pct"),
        "P/L 7 Giorni": t("col_pl_7d"),
        "P/L 7 Giorni %": t("col_pl_7d_pct"),
        "AvgCostBefore": t("col_avg_cost_before"),
        "RealizedTradePL": t("col_realized_trade_pl"),

        # flows / xirr
        "Operazioni": t("col_flow_operations"),
        "Dividendi": t("col_flow_dividends"),
        "Valore finale": t("col_flow_final_value"),
        "Totale": t("col_flow_total"),

        # show_all extra
        "ID": t("col_id"),
        "SpeseEuro": t("col_fees_eur"),
        "Tassa": t("col_tax"),
        "Cambio": t("col_fx"),
        "FlussoNetto": t("col_cashflow"),
        "Prezzo medio s/carico": t("col_avg_cost_trade"),
        "PositionKey": t("col_position_key"),
        "_rowid": t("col_rowid"),
        "AvgCostAfter": t("col_avg_cost_after"),
        "QtyOpenAfter": t("col_qty_open_after"),
        "CostOpenAfter": t("col_cost_open_after"),
        "CashflowCalc": t("col_cashflow_calc"),
        "TaxEuroCalc": t("col_tax_calc"),
        
        "Valore portafoglio": t("col_portfolio_value"),
        "Capitale investito": t("col_invested_capital"),
        "P/L trading": t("col_trading_pl"),
    }


def get_format_dict(df_base, columns_map=None, lang=None):
    """
    Costruisce automaticamente il dizionario di formattazione
    per le colonne di un DataFrame già basato su nomi interni.

    df_base: DataFrame con nomi colonna originali/interi
    columns_map: mapping interno -> label tradotta
    lang: opzionale ("it" / "en"), se None prende session_state
    """
    if columns_map is None:
        columns_map = get_display_columns()

    if lang is None:
        lang = st.session_state.get("lang", "it")

    date_fmt = "{:%d/%m/%Y}" if lang == "it" else "{:%Y-%m-%d}"

    fmt_dict = {}

    for col in df_base.columns:
        col_lower = str(col).strip().lower()
        display_col = columns_map.get(col, col)

        # 1) date
        if col_lower == "data":
            fmt_dict[display_col] = date_fmt

        # ID
        elif col_lower == "id":
            fmt_dict[display_col] = "{:,.0f}"
        
        # ✅ TASSA PRIMA del blocco euro
        elif col_lower in ["tassa", "tax"]:
            fmt_dict[display_col] = "{:.2%}"

        # 2) quantità
        elif any(k in col_lower for k in ["quant", "qty", "quantity"]):
            fmt_dict[display_col] = "{:,.2f}"

        # 3) percentuali
        elif "%" in str(col):
            fmt_dict[display_col] = "{:.2%}"

        # 4) prezzi / costi / cambio
        elif any(k in col_lower for k in [
            "prezzo", "price", "cost", "avgcost", "costo", "cambio", "fx"
        ]):
            fmt_dict[display_col] = "{:,.2f}"

        # 5) valori monetari / pl / flow / tax / dividends
        elif any(k in col_lower for k in [
            "pl", "valore", "flow", "cashflow", "tax", "div", "spese", "fees"
        ]):
            fmt_dict[display_col] = "€ {:,.2f}"

    return fmt_dict

def get_format_dict_positions(df_base, columns_map=None, lang=None):

    if columns_map is None:
        from utils.display import get_display_columns
        columns_map = get_display_columns()

    if lang is None:
        lang = st.session_state.get("lang", "it")

    # ✅ formato data per lingua
    date_fmt = "{:%d/%m/%Y}" if lang == "it" else "{:%Y-%m-%d}"

    fmt = {}

    for col in df_base.columns:
        col_lower = str(col).strip().lower()
        display_col = columns_map.get(col, col)

        # =========================
        # ✅ DATA
        # =========================
        if col_lower == "data":
            fmt[display_col] = date_fmt

        # =========================
        # ✅ ID (intero)
        # =========================
        elif col_lower == "id":
            fmt[display_col] = "{:,.0f}"

        # =========================
        # ✅ QUANTITÀ
        # =========================
        elif any(k in col_lower for k in ["quant", "qty", "quantity"]):
            fmt[display_col] = "{:,.2f}"

        # =========================
        # ✅ PERCENTUALI (incl. Tassa)
        # =========================
        elif col_lower in ["p/l %", "p/l giornaliero %", "p/l 7 giorni %", "tassa", "tax"]:
            fmt[display_col] = "{:.2%}"

        # =========================
        # ✅ PREZZI / COSTI
        # =========================
        elif any(k in col_lower for k in [
            "prezzo", "price", "cost", "avgcost", "costo"
        ]):
            fmt[display_col] = "{:,.2f}"

        # =========================
        # ✅ VALORI IN EURO
        # =========================
        elif any(k in col_lower for k in [
            "valore",       # Value
            "pl",           # P/L
            "div",          # Dividends
            "spese",        # Fees
            "flow",         # Cashflow
            "cash",         # CashflowCalc
            "taxeuro",      # TaxEuroCalc (IMPORTANTE!)
        ]):
            fmt[display_col] = "€ {:,.2f}"

        # =========================
        # ✅ FALLBACK NUMERICO
        # =========================
        elif pd.api.types.is_numeric_dtype(df_base[col]):
            fmt[display_col] = "{:,.2f}"

    return fmt
