from utils.i18n import t

def get_display_columns():
    return {
        "Ticker": t("col_ticker"),
        "Intermediario": t("col_broker"),
        "Nome": t("col_name"),
        "Tipo": t("col_type"),
        "Area": t("col_area"),
        "Settore": t("col_sector"),
        "Emittente": t("col_issuer"),
        "Valuta": t("col_currency"),
        "Quantita": t("col_quantity"),
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
        
        # ✅ AGGIUNTA per operations preview
        "Data": t("col_date"),
        "Prezzo": t("col_trade_price"),
        "AvgCostBefore": t("col_avg_cost_before"),
        "RealizedTradePL": t("col_realized_trade_pl"),
    }
