from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
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
    Cost engine (step 1):
    - supporto LONG ✅
    - supporto apertura SHORT ✅
    - chiusura short NON ancora gestita (step 2)
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
            cashflow = 0.0

            # =========================
            # ✅ BUY
            # =========================
            if qty > 0:
            
                # ✅ CHIUSURA SHORT
                if open_qty < 0:
                    close_qty = min(abs(open_qty), qty)
            
                    avg_cost_short = abs(avg_cost_before)
            
                    cost_basis = close_qty * avg_cost_short
                    buy_cost = close_qty * price * fx
            
                    realized_gross = cost_basis - buy_cost
            
                    tax_euro = max(realized_gross, 0.0) * tax_rate
                    cashflow = -(buy_cost + fees + tax_euro)
            
                    realized_trade_pl = realized_gross - tax_euro
            
                    open_qty += close_qty
                    open_cost += cost_basis
            
                    # eventuale long residuo
                    remaining_qty = qty - close_qty
            
                    if remaining_qty > 0:
                        buy_cost_extra = remaining_qty * price * fx + fees
                        open_qty += remaining_qty
                        open_cost += buy_cost_extra
            
                else:
                    # ✅ ACQUISTO LONG
                    buy_cost = qty * price * fx + fees
                    open_qty += qty
                    open_cost += buy_cost
            
                    cashflow = -buy_cost

            # =========================
            # ✅ SELL
            # =========================
            elif qty < 0:
                sell_qty = abs(qty)
            
                # ✅ SHORT (open o estensione)
                if open_qty <= 0:
                    gross_proceeds = sell_qty * price * fx
            
                    cashflow = gross_proceeds - fees
                    realized_trade_pl = 0.0
            
                    open_qty -= sell_qty
                    open_cost -= gross_proceeds
            
                else:
                    # ✅ CHIUSURA LONG
                    cost_basis_sold = sell_qty * avg_cost_before
            
                    gross_proceeds = sell_qty * price * fx
                    realized_gross = gross_proceeds - fees - cost_basis_sold
            
                    tax_euro = max(realized_gross, 0.0) * tax_rate
                    cashflow = gross_proceeds - fees - tax_euro
            
                    realized_trade_pl = realized_gross - tax_euro
            
                    open_qty -= sell_qty
                    open_cost -= cost_basis_sold

                    # pulizia floating
                    if abs(open_qty) < 1e-12:
                        open_qty = 0.0
                    if abs(open_cost) < 1e-12:
                        open_cost = 0.0

            # =========================
            # qty == 0
            # =========================
            else:
                cashflow = 0.0

            # =========================
            # ✅ DEBUG (puoi attivarlo)
            # =========================
            # st.write({
            #     "Data": row["Data"],
            #     "qty": qty,
            #     "open_qty": open_qty,
            #     "open_cost": open_cost,
            #     "avg_cost_before": avg_cost_before,
            #     "cashflow": cashflow,
            #     "realized": realized_trade_pl
            # })

            avg_cost_after = open_cost / open_qty if open_qty != 0 else 0.0

            # salva
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

    # prezzo medio fallback
    if "Prezzo medio s/carico" in ops.columns:
        ops["Prezzo medio s/carico"] = ops["Prezzo medio s/carico"].fillna(ops["AvgCostAfter"])
    else:
        ops["Prezzo medio s/carico"] = ops["AvgCostAfter"]

    return ops

def build_portfolio(ops: pd.DataFrame, closes: pd.DataFrame, dividends: pd.DataFrame | None = None):

    # ✅ normalizzazione date
    ops_all = ops.copy()
    ops_all["Data"] = pd.to_datetime(ops_all["Data"], errors="coerce")
    ops_all["DateOnly"] = ops_all["Data"].dt.normalize()

    if ops_all.empty:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame()
        )

    # =========================
    # 1. Arricchimento cost engine
    # =========================
    ops_all = enrich_ops_with_cost_engine(ops_all)

    # st.write("OPS_ALL")
    # st.dataframe(
    #     ops_all[
    #         [
    #             "Data",
    #             "Ticker",
    #             "Quantita",
    #             "QtyOpenAfter",
    #             "CostOpenAfter",
    #             "CashflowCalc",
    #             "RealizedTradePL"
    #         ]
    #     ]
    # )

    # =========================
    # 2. Ticker validi (solo quelli con prezzi disponibili)
    # =========================
    valid_tickers = [t for t in ops_all["Ticker"].unique() if t in closes.columns]
    ops = ops_all[ops_all["Ticker"].isin(valid_tickers)].copy()

    # Se non ho nemmeno date valide, esco
    if ops_all["Data"].dropna().empty:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame()
        )

    # =========================
    # 3. Costruzione indice temporale completo
    # =========================
    # start_date = ops_all["Data"].min().normalize()
    # end_date = closes.index.max()
    
    today = pd.Timestamp.today().normalize()
    start_date = ops_all["DateOnly"].min() - pd.Timedelta(days=5)
    end_date = today
    
    market_last_date = closes.index.max()
    
    idx = pd.date_range(start=start_date, end=market_last_date, freq="D")

    # =========================
    # 4. Se non ci sono ticker validi, costruisco serie vuote
    # =========================
    if ops.empty:
        holdings = pd.DataFrame(index=idx)
        position_closes_eur = pd.DataFrame(index=idx)
        position_values = pd.DataFrame(index=idx)
        total_value = pd.Series(np.nan, index=idx, name="Valore portafoglio")
    else:
        # =========================
        # 5. Quantità storiche coerenti con il cost engine
        # =========================
        qty_history = (
            ops.sort_values(["PositionKey", "Data"])
            .groupby(["PositionKey", "Data"])["QtyOpenAfter"]
            .last()
            .unstack(level=0)
            .reindex(idx)
            .ffill()
        )

        qty_history = qty_history.fillna(0.0)

        # Manteniamo il nome "holdings" per compatibilità
        holdings = qty_history.copy()

        # =========================
        # 6. Prezzi ticker / conversione EUR
        # =========================
        closes_ticker = (
            closes[valid_tickers]
            .reindex(idx)
            .ffill()
        )

        closes_eur_ticker, _ = convert_closes_to_eur(
            closes_ticker,
            ops,
            start_date,
            market_last_date
        )

        # =========================
        # 7. Prezzi EUR per PositionKey
        # =========================
        position_to_ticker = ops.groupby("PositionKey")["Ticker"].last()
        position_closes_eur = pd.DataFrame(index=idx)

        for pos_key in holdings.columns:
            ticker = position_to_ticker.loc[pos_key]
            if ticker in closes_eur_ticker.columns:
                position_closes_eur[pos_key] = closes_eur_ticker[ticker]

        position_closes_eur = position_closes_eur.reindex(columns=holdings.columns)

        # =========================
        # 8. Valore storico portafoglio
        # =========================
        position_values = holdings * position_closes_eur

        # min_count=1 evita che tutte-NaN diventino 0
        total_value = position_values.sum(axis=1, min_count=1).rename("Valore portafoglio")

    # =========================
    # 9. Cashflow / realized su tutte le operazioni
    # =========================
    ops_cf = ops_all.copy()
    ops_cf["Cashflow"] = ops_cf["CashflowCalc"]

    if dividends is None or dividends.empty:
        daily_dividends = pd.Series(0.0, index=idx, name="Dividendi netti")
    else:
        dividends = dividends.copy()
        dividends["DateOnly"] = pd.to_datetime(dividends["Data"], errors="coerce").dt.normalize()
        
        daily_dividends = (
            dividends.groupby("DateOnly")["DividendoNetto"]
            .sum()
            .reindex(idx, fill_value=0.0)
            .rename("Dividendi netti")
        )

    # sell_ops = ops_cf.loc[ops_cf["Quantita"] < 0].copy()

    # realized_from_trades = (
    #     sell_ops.groupby("DateOnly")["RealizedTradePL"]
    #     .sum()
    #     .reindex(idx, fill_value=0.0)
    # )
    
    realized_from_trades = (
        ops_cf.groupby("DateOnly")["RealizedTradePL"]
        .sum()
        .reindex(idx, fill_value=0.0)
    )

    realized_daily = realized_from_trades.add(daily_dividends, fill_value=0.0)
    pl_realizzato = realized_daily.cumsum().rename("P/L realizzato")
    
    # =========================
    # 10. Capitale investito reale (costo residuo aperto storico)
    # =========================
    if ops.empty:
        invested = pd.Series(0.0, index=idx, name="Capitale investito")
    else:
        cost_history = (
            ops.sort_values(["PositionKey", "Data"])
            .groupby(["PositionKey", "Data"])["CostOpenAfter"]
            .last()
            .unstack(level=0)
            .reindex(idx)
            .ffill()
        )

        cost_history = cost_history.fillna(0.0)
        invested = cost_history.sum(axis=1).rename("Capitale investito")

    # =========================
    # 11. Capitale versato (flussi netti cumulati)
    # =========================
    daily_cf_total = (
        ops_cf.groupby("DateOnly")["Cashflow"]
        .sum()
        .reindex(idx, fill_value=0.0)
    )

    capital_versato = (-daily_cf_total.cumsum()).rename("Capitale versato")

    # =========================
    # 12. P/L giornaliero per posizione
    # =========================
    if ops.empty:
        daily_pl_positions = pd.DataFrame(index=idx)
        weekly_pl_positions = pd.DataFrame(index=idx)
        monthly_pl_positions = pd.DataFrame(index=idx)
        daily_pl = pd.Series(0.0, index=idx, name="P/L Giornaliero")
        daily_pl_pct = pd.Series(np.nan, index=idx, name="P/L Giornaliero %")
        
        weekly_pl = pd.Series(0.0, index=idx, name="P/L 7 Giorni")
        weekly_pl_pct = pd.Series(np.nan, index=idx, name="P/L 7 Giorni %")
    else:
        
        daily_cf_positions = (
            ops_cf.groupby(["DateOnly", "PositionKey"])["Cashflow"]
            .sum()
            .unstack(fill_value=0.0)
            .reindex(index=idx, columns=holdings.columns, fill_value=0.0)
        )

        # debug
        # st.write("CLOSES RAW")
        # st.dataframe(
        #     closes.loc["2026-06-30":"2026-07-02", ["LDO.MI"]]
        # )
        
        # st.write("CLOSES_TICKER")
        # st.dataframe(
        #     closes_ticker.loc["2026-06-30":"2026-07-02"]
        # )
        
        # st.write("CLOSES_EUR_TICKER")
        # st.dataframe(
        #     closes_eur_ticker.loc["2026-06-30":"2026-07-02"]
        # )
        
        # st.write("POSITION_CLOSES_EUR")
        # st.dataframe(
        #     position_closes_eur.loc["2026-06-30":"2026-07-02"]
        # )
        
        # st.write("position_values")
        # st.write(position_values.tail(10))
        
        # st.write("position_values.diff()")
        # st.write(position_values.diff().tail(10))
        
        # st.write("daily_cf_positions")
        # st.write(daily_cf_positions.tail(10))

        # daily_pl_positions = (
        #     position_values.diff().fillna(0.0)
        #     .add(daily_cf_positions, fill_value=0.0)
        # )

        market_move = position_values.diff()
        
        first_day = (
            position_values.notna()
            & position_values.shift(1).isna()
        )
        
        market_move[first_day] = position_values[first_day]
        
        daily_pl_positions = (
            market_move
            .add(daily_cf_positions, fill_value=0.0)
        )
        
        weekly_pl_positions = (
            daily_pl_positions
            .rolling("7D")
            .sum()
        )
        
        monthly_pl_positions = (
            daily_pl_positions
            .rolling("30D")
            .sum()
        )
        
        daily_pl = daily_pl_positions.sum(axis=1).rename("P/L Giornaliero")
        daily_pl_pct = (daily_pl / total_value.shift(1)).rename("P/L Giornaliero %")
        
        # P/L rolling 7 giorni
        weekly_pl = (
            daily_pl
            .rolling("7D")
            .sum()
            .rename("P/L 7 Giorni")
        )
        
        weekly_pl_pct = (
            weekly_pl
            / total_value.shift(7)
        ).rename("P/L 7 Giorni %")

         # P/L rolling 30 days
        monthly_pl = (
            daily_pl
            .rolling("30D")
            .sum()
            .rename("P/L 30 Giorni")
        )
        
        monthly_pl_pct = (
            monthly_pl
            / total_value.shift(30)
        ).rename("P/L 30 Giorni %")

        # ==================================================
        # Performance totale portafoglio
        # (unrealized + realized + dividendi)
        # ==================================================
        
        daily_total_pl = (
            daily_pl + realized_daily
        ).rename("P/L Totale Giornaliero")
        
        daily_total_pl_pct = (
            daily_total_pl / total_value.shift(1)
        ).rename("P/L Totale Giornaliero %")
        
        weekly_total_pl = (
            daily_total_pl
            .rolling("7D")
            .sum()
            .rename("P/L Totale 7 Giorni")
        )
        
        weekly_total_pl_pct = (
            weekly_total_pl / total_value.shift(7)
        ).rename("P/L Totale 7 Giorni %")
        
        monthly_total_pl = (
            daily_total_pl
            .rolling("30D")
            .sum()
            .rename("P/L Totale 30 Giorni")
        )
        
        monthly_total_pl_pct = (
            monthly_total_pl / total_value.shift(30)
        ).rename("P/L Totale 30 Giorni %")
        
    # =========================
    # 13. P/L trading = valore portafoglio - costo residuo aperto
    # =========================
    pnl = (total_value - invested).rename("P/L trading")

    # =========================
    # 14. Serie storica finale
    # =========================
    ts = pd.concat(
        [
            total_value,
            invested,
            capital_versato,
            pnl,
            daily_pl,
            daily_pl_pct,
            weekly_pl,
            weekly_pl_pct,
            monthly_pl,
            monthly_pl_pct,
            daily_total_pl,
            daily_total_pl_pct,
            weekly_total_pl,
            weekly_total_pl_pct,
            monthly_total_pl,
            monthly_total_pl_pct,
            daily_dividends,
            pl_realizzato
        ],
        axis=1
    )

    # =========================
    # 15. Se non ci sono ticker validi → niente current/exposure
    # =========================
    if ops.empty:
        current = pd.DataFrame()
        exposure = pd.DataFrame()
        return ts, current, holdings, exposure, ops_all

    # =========================
    # 16. Metadati posizioni
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
    # 17. Stato attuale posizioni aperte
    # =========================
    # ✅ usa la quantità residua reale del motore costi
    last_qty = cost_state["NetQty"]
    last_close_eur = position_closes_eur.iloc[-1]
    last_daily_pl = daily_pl_positions.iloc[-1]
    last_weekly_pl = weekly_pl_positions.iloc[-1]
    last_monthly_pl = monthly_pl_positions.iloc[-1]

   
    # last_qty = cost_state["NetQty"]
    # last_close_eur = position_closes_eur.iloc[-1]
    # last_daily_pl = daily_pl_positions.iloc[-1]

    current = pd.concat([
        last_qty.rename("Quantita"),
        last_close_eur.rename("Prezzo Attuale"),
        last_daily_pl.rename("P/L Giornaliero"),
        last_weekly_pl.rename("P/L 7 Giorni"),
        last_monthly_pl.rename("P/L 30 Giorni"),
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
    current["P/L 7 Giorni %"] = current.apply(
        lambda row: row["P/L 7 Giorni"] / (row["Valore"] - row["P/L 7 Giorni"])
        if (row["Valore"] - row["P/L 7 Giorni"]) != 0 else np.nan,
        axis=1
    )
    current["P/L 30 Giorni %"] = current.apply(
        lambda row: row["P/L 30 Giorni"] / (row["Valore"] - row["P/L 30 Giorni"])
        if (row["Valore"] - row["P/L 30 Giorni"]) != 0 else np.nan,
        axis=1
    )
    
    current = current.copy()

    # =========================
    # 18. Dividendi incassati per posizione
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
    current = current[
        (current["Quantita"].abs() > 1e-12) &
        (current["Prezzo Attuale"].notna())
    ].sort_values("Valore", ascending=False)

    exposure = current.reset_index().rename(columns={"index": "PositionKey"})

    return ts, current, holdings, exposure, ops_all
