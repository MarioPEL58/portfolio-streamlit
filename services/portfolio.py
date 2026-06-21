from __future__ import annotations

import numpy as np
import pandas as pd

from services.market_data import convert_closes_to_eur


def build_holdings(ops: pd.DataFrame, idx: pd.DatetimeIndex) -> pd.DataFrame:
    keys = sorted(ops["PositionKey"].unique().tolist())
    holdings = pd.DataFrame(0.0, index=idx, columns=keys)

    daily_ops = ops.groupby(["Data", "PositionKey"], as_index=False)["Quantita"].sum()

    for key in keys:
        s = (
            daily_ops[daily_ops["PositionKey"] == key]
            .set_index("Data")["Quantita"]
            .sort_index()
        )
        holdings[key] = s.reindex(idx, fill_value=0).cumsum()

    return holdings
def enrich_ops_with_cost_engine(ops: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola in Python, per ogni operazione:
    - AvgCostBefore
    - AvgCostAfter
    - CostOpenAfter
    - QtyOpenAfter
    - CashflowCalc
    - RealizedTradePL

    Logica:
    - acquisto: aumenta quantità e costo residuo
    - vendita: realizza P/L sul costo medio residuo
    - tassa applicata solo a vendite con profitto positivo
    """

    ops = ops.copy().sort_values(["PositionKey", "Data"]).reset_index(drop=True)
    ops["_rowid"] = np.arange(len(ops))

    # sicurezza
    ops["Quantita"] = ops["Quantita"].fillna(0.0)
    ops["Prezzo"] = ops["Prezzo"].fillna(0.0)
    ops["Cambio"] = ops["Cambio"].fillna(1.0)
    ops["SpeseEuro"] = ops["SpeseEuro"].fillna(0.0)
    ops["Tassa"] = ops["Tassa"].fillna(0.0)

    avg_before_list = []
    avg_after_list = []
    qty_after_list = []
    cost_after_list = []
    realized_list = []
    cashflow_list = []
    tax_euro_list = []

    for pos_key, grp in ops.groupby("PositionKey", sort=False):
        open_qty = 0.0
        open_cost = 0.0

        for _, row in grp.iterrows():
            qty = float(row["Quantita"])
            price = float(row["Prezzo"])
            fx = float(row["Cambio"])
            fees = float(row["SpeseEuro"])
            tax_rate = float(row["Tassa"])

            avg_cost_before = open_cost / open_qty if open_qty != 0 else 0.0
            realized_trade_pl = 0.0
            tax_euro = 0.0

            if qty > 0:
                # ACQUISTO
                buy_cost = qty * price * fx + fees
                open_qty = open_qty + qty
                open_cost = open_cost + buy_cost

                cashflow = -buy_cost

            elif qty < 0:
                # VENDITA
                sell_qty = abs(qty)

                # costo storico della quantità venduta
                cost_basis_sold = sell_qty * avg_cost_before

                gross_proceeds = sell_qty * price * fx
                realized_gross = gross_proceeds - fees - cost_basis_sold

                # tassa solo su profitto positivo
                tax_euro = max(realized_gross, 0.0) * tax_rate

                # cashflow netto vendita
                cashflow = gross_proceeds - fees - tax_euro

                realized_trade_pl = cashflow - cost_basis_sold

                # scarico costo residuo
                open_qty = open_qty - sell_qty
                open_cost = open_cost - cost_basis_sold

                # anti floating residuals
                if abs(open_qty) < 1e-12:
                    open_qty = 0.0
                if abs(open_cost) < 1e-12:
                    open_cost = 0.0

            else:
                # qty == 0
                cashflow = 0.0

            avg_cost_after = open_cost / open_qty if open_qty != 0 else 0.0

            avg_before_list.append(avg_cost_before)
            avg_after_list.append(avg_cost_after)
            qty_after_list.append(open_qty)
            cost_after_list.append(open_cost)
            realized_list.append(realized_trade_pl)
            cashflow_list.append(cashflow)
            tax_euro_list.append(tax_euro)

    ops["AvgCostBefore"] = avg_before_list
    ops["AvgCostAfter"] = avg_after_list
    ops["QtyOpenAfter"] = qty_after_list
    ops["CostOpenAfter"] = cost_after_list
    ops["RealizedTradePL"] = realized_list
    ops["CashflowCalc"] = cashflow_list
    ops["TaxEuroCalc"] = tax_euro_list

    # ✅ Prezzo medio s/carico:
    # se esiste nel file → lo mantieni
    # se manca → lo calcoli dal cost engine
    
    if "Prezzo medio s/carico" in ops.columns:
        ops["Prezzo medio s/carico"] = ops["Prezzo medio s/carico"].fillna(ops["AvgCostAfter"])
    else:
        ops["Prezzo medio s/carico"] = ops["AvgCostAfter"]

    return ops

def build_portfolio(ops: pd.DataFrame, closes: pd.DataFrame, dividends: pd.DataFrame | None = None):

    ops_all = ops.copy()

    if ops_all.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # =========================
    # 1. Arricchimento cost engine
    # =========================
    ops_all = enrich_ops_with_cost_engine(ops_all)

    # =========================
    # 2. Ticker validi (solo quelli con prezzi disponibili)
    # =========================
    valid_tickers = [t for t in ops_all["Ticker"].unique() if t in closes.columns]
    ops = ops_all[ops_all["Ticker"].isin(valid_tickers)].copy()

    if ops.empty:
        idx = pd.DatetimeIndex(sorted(ops_all["Data"].dropna().unique()))
        if len(idx) == 0:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    else:
        idx = closes.index

    # =========================
    # 3. Quantità storiche coerenti con il cost engine
    #    (invece di  su Quantita)
    # =========================
    qty_history = (
        ops.sort_values(["PositionKey", "Data"])
        .groupby(["Data", "PositionKey"])["QtyOpenAfter"]
        .last()
        .unstack(fill_value=np.nan)
        .reindex(idx)
        .ffill()
        .fillna(0.0)
    )

    # manteniamo il nome holdings per compatibilità col resto della app
    holdings = qty_history.copy()

    # =========================
    # 4. Prezzi ticker / conversione EUR
    # =========================
    closes_ticker = closes[valid_tickers].reindex(idx).ffill()

    start_date = ops["Data"].min().normalize()
    end_date = pd.Timestamp.today().normalize()

    closes_eur_ticker, _ = convert_closes_to_eur(
        closes_ticker,
        ops,
        start_date,
        end_date
    )

    # =========================
    # 5. Prezzi EUR per PositionKey
    # =========================
    position_to_ticker = ops.groupby("PositionKey")["Ticker"].last()
    position_closes_eur = pd.DataFrame(index=idx)

    for pos_key in holdings.columns:
        ticker = position_to_ticker.loc[pos_key]
        if ticker in closes_eur_ticker.columns:
            position_closes_eur[pos_key] = closes_eur_ticker[ticker]

    position_closes_eur = position_closes_eur.reindex(columns=holdings.columns)

    # =========================
    # 6. Valore storico portafoglio
    # =========================
    position_values = holdings * position_closes_eur
    total_value = position_values.sum(axis=1).rename("Valore portafoglio")

    # =========================
    # 7. Cashflow / realized su tutte le operazioni
    # =========================
    ops_cf = ops_all.copy()
    ops_cf["Cashflow"] = ops_cf["CashflowCalc"]

    if dividends is None or dividends.empty:
        daily_dividends = pd.Series(0.0, index=idx, name="Dividendi netti")
    else:
        daily_dividends = (
            dividends.groupby("Data")["DividendoNetto"]
            .sum()
            .reindex(idx, fill_value=0.0)
            .rename("Dividendi netti")
        )

    sell_ops = ops_cf.loc[ops_cf["Quantita"] < 0].copy()

    realized_from_trades = (
        sell_ops.groupby("Data")["RealizedTradePL"]
        .sum()
        .reindex(idx, fill_value=0.0)
    )

    realized_daily = realized_from_trades.add(daily_dividends, fill_value=0.0)
    pl_realizzato = realized_daily.cumsum().rename("P/L realizzato")

    # =========================
    # 8. Flussi netti cumulati
    # =========================
    daily_cf_total = (
        ops_cf.groupby("Data")["Cashflow"]
        .sum()
        .reindex(idx, fill_value=0.0)
    )

    invested = daily_cf_total.cumsum().rename("Capitale investito")

    # =========================
    # 9. P/L giornaliero per posizione
    # =========================
    daily_cf_positions = (
        ops_cf.groupby(["Data", "PositionKey"])["Cashflow"]
        .sum()
        .unstack(fill_value=0.0)
        .reindex(index=idx, columns=holdings.columns, fill_value=0.0)
    )

    daily_pl_positions = (
        position_values.diff().fillna(0.0)
        .add(daily_cf_positions, fill_value=0.0)
    )

    daily_pl = daily_pl_positions.sum(axis=1).rename("P/L Giornaliero")
    daily_pl_pct = (daily_pl / total_value.shift(1)).rename("P/L Giornaliero %")

    # P/L trading = realized + unrealized (ESCLUSI dividendi)
    pnl = (total_value + invested).rename("P/L trading")

    # =========================
    # 10. Serie storica finale
    # =========================
    ts = pd.concat(
        [total_value, invested, pnl, daily_pl, daily_pl_pct, daily_dividends, pl_realizzato],
        axis=1
    )

    # =========================
    # 11. Metadati posizioni
    # =========================
    meta = (
        ops.sort_values("Data")
        .groupby("PositionKey")
        .agg({
            "ID": "last",
            "Ticker": "last",
            "Intermediario": "last",
            "Nome": "last",
            "Tipo": "last",
            "Area": "last",
            "Settore": "last",
            "Emittente": "last",
            "Valuta": "last",
            "Tassa": "last",
        })
    )

    cost_state = (
        ops.groupby("PositionKey")
        .agg(
            NetQty=("QtyOpenAfter", "last"),
            OpenCost=("CostOpenAfter", "last"),
            AvgCost=("AvgCostAfter", "last"),
        )
    )

    # =========================
    # 12. Stato attuale posizioni aperte
    # =========================
    last_qty = cost_state["NetQty"]
    last_close_eur = position_closes_eur.iloc[-1]
    last_daily_pl = daily_pl_positions.iloc[-1]

    current = pd.concat([
        last_qty.rename("Quantita"),
        last_close_eur.rename("Prezzo Attuale"),
        last_daily_pl.rename("P/L Giornaliero"),
    ], axis=1)

    current["Ultimo Close Storico"] = last_close_eur
    current["Valore"] = current["Quantita"] * current["Prezzo Attuale"]

    current = current.join(cost_state, how="left").join(meta, how="left")

    current["Costo Medio Stimato"] = current["AvgCost"]
    current["Costo Totale Stimato"] = current["OpenCost"]

    current["P/L"] = current["Valore"] - current["Costo Totale Stimato"]

    current["P/L %"] = np.where(
        current["Costo Totale Stimato"] != 0,
        current["P/L"] / current["Costo Totale Stimato"],
        np.nan
    )

    current["TaxRate"] = current["Tassa"].fillna(0.26)
    current["P/L Netto Stimato"] = current.apply(
        lambda row: row["P/L"] * (1 - row["TaxRate"]) if row["P/L"] > 0 else row["P/L"],
        axis=1
    )

    current["P/L Giornaliero %"] = current.apply(
        lambda row: row["P/L Giornaliero"] / (row["Valore"] - row["P/L Giornaliero"])
        if (row["Valore"] - row["P/L Giornaliero"]) != 0 else np.nan,
        axis=1
    )

    current = current.copy()

    # =========================
    # 13. Dividendi incassati per posizione
    # =========================
    if dividends is not None and not dividends.empty:
        dividends = dividends.copy()

        current["ID"] = current["ID"].astype("Int64", errors="ignore")
        dividends["ID"] = dividends["ID"].astype("Int64", errors="ignore")

        current["ID"] = current["ID"].astype(str).str.strip()
        dividends["ID"] = dividends["ID"].astype(str).str.strip()

        dividends_by_position = (
            dividends.groupby("ID")["DividendoNetto"]
            .sum()
            .rename("Dividendi Netti Incassati")
        )

        current = current.join(dividends_by_position, on="ID")
        current["Dividendi Netti Incassati"] = current["Dividendi Netti Incassati"].fillna(0.0)
    else:
        current["Dividendi Netti Incassati"] = 0.0

    # filtro posizioni realmente aperte
    current = current[current["Quantita"].abs() > 1e-12].sort_values("Valore", ascending=False)

    exposure = current.reset_index().rename(columns={"index": "PositionKey"})

    return ts, current, holdings, exposure, ops_all
