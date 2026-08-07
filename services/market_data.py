from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf
import numpy as np
from pathlib import Path

@st.cache_data(show_spinner=False)
def download_close_prices(tickers: list[str], start_date: pd.Timestamp, end_date: pd.Timestamp):
    tickers = [t for t in tickers if isinstance(t, str) and t.strip()]
    if not tickers:
        return pd.DataFrame(), []

    raw = yf.download(
        tickers=tickers,
        start=start_date.strftime("%Y-%m-%d"),
        end=(end_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
        auto_adjust=False,
        progress=False,
        group_by="ticker",
        threads=True,
    )
    
    # st.write("START", start_date.strftime("%Y-%m-%d"))
    # st.write("END", (end_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"))
    # st.write(raw)
    st.write(raw.columns)
    st.write(closes["IT0005494239"].dropna().tail())


    if raw is None or len(raw) == 0:
        return pd.DataFrame(), tickers

    closes = pd.DataFrame(index=raw.index)

    if isinstance(raw.columns, pd.MultiIndex):
        lvl0 = set(raw.columns.get_level_values(0))

        if all(t in lvl0 for t in tickers):
            for t in tickers:
                if "Close" in raw[t].columns:
                    closes[t] = raw[t]["Close"]
                elif "Adj Close" in raw[t].columns:
                    closes[t] = raw[t]["Adj Close"]
        else:
            field = "Close" if "Close" in lvl0 else ("Adj Close" if "Adj Close" in lvl0 else None)
            if field is not None:
                sub = raw[field]
                for t in tickers:
                    if t in sub.columns:
                        closes[t] = sub[t]
    else:
        t = tickers[0]
        if "Close" in raw.columns:
            closes[t] = raw["Close"]
        elif "Adj Close" in raw.columns:
            closes[t] = raw["Adj Close"]

    closes = closes.sort_index()
    
    # =========================
    # ✅ Pulizia base
    # =========================
    closes = closes.replace([0, np.inf, -np.inf], np.nan)
    
    # =========================
    # ✅ Rimozione outlier (glitch)
    # =========================
    returns = closes.pct_change()
    
    threshold = 0.3  # 30% giornaliero
    outliers = returns.abs() > threshold
    
    closes[outliers] = np.nan
    
    # =========================
    # ✅ Fill
    # =========================
    closes = closes.ffill()
    
    # =========================
    # ✅ Controllo qualità
    # =========================
    invalid_points = outliers.sum().sum()
    
    if invalid_points > 0:
        st.caption(f"⚠️ Correzione automatica di {invalid_points} prezzi anomali")
    
    # =========================
    # ✅ Missing ticker
    # =========================
    st.write("Ticker richiesti:", tickers)
    st.write("Ticker trovati:", closes.columns.tolist())

    missing = [t for t in tickers if t not in closes.columns]
    
    st.write("Ticker mancanti:", missing)
    
    return closes, missing


@st.cache_data(show_spinner=False)
def download_fx_series(currencies: list[str], start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    currencies = sorted(set([c for c in currencies if isinstance(c, str) and c and c != "EUR"]))
    if not currencies:
        return pd.DataFrame()

    yahoo_pairs = {ccy: f"EUR{ccy}=X" for ccy in currencies}

    raw = yf.download(
        tickers=list(yahoo_pairs.values()),
        start=start_date.strftime("%Y-%m-%d"),
        end=(end_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
        auto_adjust=False,
        progress=False,
        group_by="ticker",
        threads=True,
    )

    if raw is None or len(raw) == 0:
        return pd.DataFrame()

    fx = pd.DataFrame(index=raw.index)

    for ccy, pair in yahoo_pairs.items():
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                lvl0 = set(raw.columns.get_level_values(0))

                if pair in lvl0:
                    if "Close" in raw[pair].columns:
                        fx[ccy] = raw[pair]["Close"]
                    elif "Adj Close" in raw[pair].columns:
                        fx[ccy] = raw[pair]["Adj Close"]
                else:
                    if "Close" in lvl0 and pair in raw["Close"].columns:
                        fx[ccy] = raw["Close"][pair]
                    elif "Adj Close" in lvl0 and pair in raw["Adj Close"].columns:
                        fx[ccy] = raw["Adj Close"][pair]
            else:
                if "Close" in raw.columns:
                    fx[ccy] = raw["Close"]
                elif "Adj Close" in raw.columns:
                    fx[ccy] = raw["Adj Close"]
        except Exception:
            pass

    fx = fx.sort_index()
    
    fx = fx.replace([0, np.inf, -np.inf], np.nan)
    
    returns = fx.pct_change()
    outliers = returns.abs() > 0.3
    
    fx[outliers] = np.nan
    fx = fx.ffill()
    
    return fx


def convert_closes_to_eur(closes: pd.DataFrame, ops: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp):
    closes_eur = closes.copy()

    ticker_ccy = (
        ops.sort_values("Data")
        .groupby("Ticker")["Valuta"]
        .last()
        .fillna("EUR")
        .to_dict()
    )

    needed_ccy = [ccy for ccy in ticker_ccy.values() if ccy != "EUR"]
    fx_rates = download_fx_series(needed_ccy, start_date, end_date)

    if fx_rates.empty:
        return closes_eur, fx_rates

    for ticker, ccy in ticker_ccy.items():
        if ticker not in closes_eur.columns or ccy == "EUR":
            continue

        if ccy in fx_rates.columns:
            fx_series = fx_rates[ccy].reindex(closes_eur.index).ffill()
            closes_eur[ticker] = closes_eur[ticker] / fx_series

    return closes_eur, fx_rates
    
@st.cache_data(show_spinner=False, ttl=120)
def download_last_intraday_timestamp(tickers: list[str]):
    tickers = [t for t in tickers if isinstance(t, str) and t.strip()]
    if not tickers:
        return None

    try:
        raw = yf.download(
            tickers=tickers,
            period="1d",
            interval="5m",
            auto_adjust=False,
            progress=False,
            group_by="ticker",
            threads=True,
            prepost=False,
        )
    except Exception:
        return None

    if raw is None or len(raw) == 0:
        return None

    timestamps = []

    try:
        if isinstance(raw.columns, pd.MultiIndex):
            lvl0 = set(raw.columns.get_level_values(0))

            # caso: MultiIndex con primo livello = ticker
            if any(t in lvl0 for t in tickers):
                for t in tickers:
                    if t in lvl0:
                        sub = raw[t]
                        col = "Close" if "Close" in sub.columns else ("Adj Close" if "Adj Close" in sub.columns else None)
                        if col is not None:
                            s = sub[col].dropna()
                            if not s.empty:
                                timestamps.append(s.index.max())

            # caso alternativo: primo livello = campo ("Close"/"Adj Close")
            else:
                field = "Close" if "Close" in lvl0 else ("Adj Close" if "Adj Close" in lvl0 else None)
                if field is not None:
                    sub = raw[field]
                    for t in tickers:
                        if t in sub.columns:
                            s = sub[t].dropna()
                            if not s.empty:
                                timestamps.append(s.index.max())

        else:
            col = "Close" if "Close" in raw.columns else ("Adj Close" if "Adj Close" in raw.columns else None)
            if col is not None:
                s = raw[col].dropna()
                if not s.empty:
                    timestamps.append(s.index.max())

    except Exception:
        return None

    if not timestamps:
        return None

    return max(timestamps)

def download_intraday_range(tickers: list[str]):

    tickers = [t for t in tickers if isinstance(t, str) and t.strip()]
    if not tickers:
        return None, None

    try:
        raw = yf.download(
            tickers=tickers,
            period="1d",
            interval="5m",
            progress=False,
            group_by="ticker"
        )
    except Exception:
        return None, None

    if raw is None or len(raw) == 0:
        return None, None

    timestamps = []

    try:
        if isinstance(raw.columns, pd.MultiIndex):
            for t in tickers:
                if t in raw.columns.get_level_values(0):
                    sub = raw[t]
                    col = "Close" if "Close" in sub.columns else None
                    if col:
                        s = sub[col].dropna()
                        if not s.empty:
                            timestamps.extend([s.index.min(), s.index.max()])
        else:
            col = "Close" if "Close" in raw.columns else None
            if col:
                s = raw[col].dropna()
                if not s.empty:
                    timestamps.extend([s.index.min(), s.index.max()])
    except Exception:
        return None, None

    if not timestamps:
        return None, None

    return min(timestamps), max(timestamps)


def load_bond_csv(isin: str) -> pd.DataFrame:

    file = Path("data/bonds") / f"{isin}.csv"

    if not file.exists():
        return pd.DataFrame()

    df = pd.read_csv(file)

    # Data tipo 07.08.2026
    df["Data"] = pd.to_datetime(
        df["Data"],
        format="%d.%m.%Y",
        errors="coerce"
    )

    # Prezzo tipo 94,880 -> 94.880
    df[isin] = (
        df["Ultimo"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    return (
        df[["Data", isin]]
        .dropna(subset=["Data"])
        .set_index("Data")
        .sort_index()
    )
