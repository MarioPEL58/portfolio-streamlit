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


def build_portfolio(ops: pd.DataFrame, closes: pd.DataFrame, dividends: pd.DataFrame | None = None):
    valid_tickers = [t for t in ops["Ticker"].unique() if t in closes.columns]
    ops = ops[ops["Ticker"].isin(valid_tickers)].copy()

    if ops.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    idx = closes.index
    holdings = build_holdings(ops, idx)

    closes_ticker = closes[valid_tickers].reindex(idx).ffill()

    start_date = ops["Data"].min().normalize()
    end_date = pd.Timestamp.today().normalize()

    closes_eur_ticker, _ = convert_closes_to_eur(
        closes_ticker,
        ops,
        start_date,
        end_date
    )

    position_to_ticker = ops.groupby("PositionKey")["Ticker"].last()
    position_closes_eur = pd.DataFrame(index=idx)

    for pos_key in holdings.columns:
        ticker = position_to_ticker.loc[pos_key]
        if ticker in closes_eur_ticker.columns:
            position_closes_eur[pos_key] = closes_eur_ticker[ticker]

    position_values = holdings * position_closes_eur
    total_value = position_values.sum(axis=1).rename("Valore portafoglio")

    ops_cf = ops.copy()
    ops_cf["Prezzo"] = ops_cf["Prezzo"].fillna(0.0)
    ops_cf["SpeseEuro"] = ops_cf["SpeseEuro"].fillna(0.0)
    ops_cf["Cambio"] = ops_cf["Cambio"].fillna(1.0)

    ops_cf["Cashflow"] = np.where(
        ops_cf["FlussoNetto"].notna(),
        ops_cf["FlussoNetto"],
        -(ops_cf["Quantita"] * ops_cf["Prezzo"] * ops_cf["Cambio"]) - ops_cf["SpeseEuro"]
    )

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
    sell_ops["RealizedTradePL"] = (
        sell_ops["FlussoNetto"]
        - (sell_ops["Quantita"].abs() * sell_ops["Prezzo medio s/carico"])
    )

    realized_from_trades = (
        sell_ops.groupby("Data")["RealizedTradePL"]
        .sum()
        .reindex(idx, fill_value=0.0)
    )

    realized_daily = realized_from_trades.add(daily_dividends, fill_value=0.0)
    pl_realizzato = realized_daily.cumsum().rename("P/L realizzato")

    daily_cf_total = (
        ops_cf.groupby("Data")["Cashflow"]
        .sum()
        .reindex(idx, fill_value=0.0)
    )

    invested = daily_cf_total.cumsum().rename("Capitale investito")

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
    pnl = (total_value + invested).rename("P/L totale")

    ts = pd.concat(
        [total_value, invested, pnl, daily_pl, daily_pl_pct, daily_dividends, pl_realizzato],
        axis=1
    )

    last_qty = holdings.iloc[-1]
    last_close_eur = position_closes_eur.iloc[-1]
    last_daily_pl = daily_pl_positions.iloc[-1]

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

    cost_df = ops.copy()
    cost_df["CostoFirmato"] = (
        (cost_df["Quantita"] * cost_df["Prezzo"].fillna(0.0))
        + cost_df["SpeseEuro"].fillna(0.0)
    )

    agg_cost = cost_df.groupby("PositionKey").agg(
        NetQty=("Quantita", "sum"),
        GrossCost=("CostoFirmato", "sum")
    )

    current = pd.concat([
        last_qty.rename("Quantita"),
        last_close_eur.rename("Prezzo Attuale"),
        last_daily_pl.rename("P/L Giornaliero"),
    ], axis=1)

    current["Ultimo Close Storico"] = last_close_eur
    current["Valore"] = current["Quantita"] * current["Prezzo Attuale"]

    current = current.join(agg_cost, how="left").join(meta, how="left")

    current["Costo Medio Stimato"] = np.where(
        current["NetQty"] != 0,
        current["GrossCost"] / current["NetQty"],
        np.nan
    )

    current["Costo Totale Stimato"] = current["Costo Medio Stimato"] * current["Quantita"]
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

    current = current[current["Quantita"] != 0].sort_values("Valore", ascending=False)
    exposure = current.reset_index().rename(columns={"index": "PositionKey"})

    return ts, current, holdings, exposure
