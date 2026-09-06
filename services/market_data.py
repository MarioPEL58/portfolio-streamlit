from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf
import numpy as np
import time
from pathlib import Path

import pytz
# 🚀 Sostituiamo requests_cache con le estensioni standard di requests
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# =====================================================================
# 🌟 CONFIGURAZIONE SESSIONE GLOBALE STANDARD (Senza cache SQLite)
# =====================================================================
# Creiamo una sessione standard per gestire i tentativi (Retry) e camuffare lo User-Agent
session = requests.Session()
retries = Retry(
    total=3,                # Numero massimo di tentativi prima di fallire
    backoff_factor=1,       # Tempo di attesa crescente tra i tentativi (1s, 2s, 4s...)
    status_forcelist=[500, 502, 503, 504] # Riprova se Yahoo risponde con questi errori di server
)
session.mount('https://', HTTPAdapter(max_retries=retries))
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

# Configurazione della cache interna nativa dei fusi orari di yfinance
yf.set_tz_cache_location("yahoo_tz_cache")

def download_close_prices(tickers: list[str], start_date: pd.Timestamp, end_date: pd.Timestamp):
    tickers = [t for t in tickers if isinstance(t, str) and t.strip()]
    if not tickers:
        return pd.DataFrame(), []
        
    yahoo_tickers = []
    isins = []
    
    for symbol in tickers:
        if is_isin(symbol):
            isins.append(symbol)
        else:
            yahoo_tickers.append(symbol)
            
    if yahoo_tickers:
        try:
            # 🚀 FIX: Passiamo la sessione standard robusta. yfinance la accetta 
            # perché non altera i meccanismi interni di memorizzazione dei dati.
            raw = yf.download(
                tickers=yahoo_tickers,
                start=start_date.strftime("%Y-%m-%d"),
                end=(end_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                auto_adjust=False,
                progress=False,
                group_by="ticker",
                threads=False,   # Manteniamo False per stabilità con le sessioni
                session=session  
            )
        except Exception as e:
            st.error(f"Errore critico durante il download da Yahoo: {e}")
            raw = pd.DataFrame()
    else: 
        raw = pd.DataFrame()

    if raw is None or len(raw) == 0:
        closes = pd.DataFrame()
    else:
        if raw.index.tz is not None:
            raw.index = raw.index.tz_localize(None)
            
        closes = pd.DataFrame(index=raw.index)
    
        if isinstance(raw.columns, pd.MultiIndex):
            lvl0 = set(raw.columns.get_level_values(0))
    
            for t in tickers:
                if t not in lvl0:
                    continue
            
                if "Close" in raw[t].columns:
                    closes[t] = raw[t]["Close"]
                elif "Adj Close" in raw[t].columns:
                    closes[t] = raw[t]["Adj Close"]
            
            if closes.empty:
                field = "Close" if "Close" in lvl0 else ("Adj Close" if "Adj Close" in lvl0 else None)
                if field is not None:
                    sub = raw[field]
                    for t in tickers:
                        if t in sub.columns:
                            closes[t] = sub[t]
        else:
            if len(tickers) > 0:
                t = tickers[0]
                if "Close" in raw.columns:
                    closes[t] = raw["Close"]
                elif "Adj Close" in raw.columns:
                    closes[t] = raw["Adj Close"]
    
        closes = closes.sort_index()
        
        # Pulizia base & Outlier
        closes = closes.replace([0, np.inf, -np.inf], np.nan)
        returns = closes.pct_change()
        threshold = 0.3  
        outliers = returns.abs() > threshold
        closes[outliers] = np.nan
        
        closes = closes.ffill()
        invalid_points = outliers.sum().sum()
        
        if invalid_points > 0:
            st.caption(f"⚠️ Correzione automatica di {invalid_points} prezzi anomali")
        
    # Missing ticker (Obbligazioni)
    missing = [t for t in tickers if (t not in closes.columns or closes[t].dropna().empty)]
    isins_caricati = []
    
    for ticker in missing:
        bond_df = load_bond_csv(ticker)
        if not bond_df.empty:
            if bond_df.index.tz is not None:
                bond_df.index = bond_df.index.tz_localize(None)
                
            isins_caricati.append(ticker)
            closes = closes.drop(columns=[ticker], errors="ignore")
            closes = closes.join(bond_df, how="outer")
    
    if isins_caricati:
        st.write(" Bond caricati bond da CSV:", ", ".join(isins_caricati))
    
    closes = closes.sort_index().ffill()
    missing = [t for t in tickers if (t not in closes.columns or closes[t].dropna().empty)]
    
    return closes, missing

# @st.cache_data(show_spinner=False)
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


# def load_bond_csv(isin: str) -> pd.DataFrame:

#     file = Path("data/bonds") / f"{isin}.csv"
#     # st.write("Cerco file:", file)
#     # st.write("Esiste?", file.exists())
    
#     if not file.exists():
#         return pd.DataFrame()

#     df = pd.read_csv(file)

#     # Data tipo 07.08.2026
#     df["Data"] = pd.to_datetime(
#         df["Data"],
#         format="%d.%m.%Y",
#         errors="coerce"
#     )

#     # Prezzo tipo 94,880 -> 94.880
#     df[isin] = (
#         df["Ultimo"]
#         .astype(str)
#         .str.replace(",", ".", regex=False)
#         .astype(float)
#     )

#     return (
#         df[["Data", isin]]
#         .dropna(subset=["Data"])
#         .set_index("Data")
#         .sort_index()
#     )

def load_bond_csv(isin: str) -> pd.DataFrame:
    file = Path("data/bonds") / f"{isin}.csv"

    if not file.exists():
        return pd.DataFrame()

    df = pd.read_csv(file)

    if "Data" in df.columns and "Ultimo" in df.columns:

        df["Data"] = pd.to_datetime(
            df["Data"],
            format="%d.%m.%Y",
            errors="coerce"
        )

        df[isin] = (
            df["Ultimo"]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )

        result = df[["Data", isin]]

    elif "Date" in df.columns and "Close" in df.columns:

        df["Date"] = pd.to_datetime(
            df["Date"],
            format="%d/%m/%Y",
            errors="coerce"
        )

        df[isin] = pd.to_numeric(df["Close"], errors="coerce")

        result = df[["Date", isin]].rename(
            columns={"Date": "Data"}
        )

    else:
        raise ValueError(
            f"Formato CSV non riconosciuto: {df.columns.tolist()}"
        )

    return (
        result
        .dropna(subset=["Data"])
        .set_index("Data")
        .sort_index()
    )

import re

ISIN_PATTERN = re.compile(
    r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$"
)

def is_isin(value: str) -> bool:
    return bool(ISIN_PATTERN.match(str(value).strip().upper()))
