from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from xml.etree.ElementPath import ops

import numpy as np
import pandas as pd # type: ignore
import plotly.express as px # type: ignore
import plotly.graph_objects as go # type: ignore
import streamlit as st # type: ignore
import yfinance as yf # type: ignore


# ============================================================
# Config
# ============================================================
st.set_page_config(
    page_title="Portfolio Tracker ETF / Azioni",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Portfolio Tracker ETF / Azioni")
st.caption(
    "Carica un file Excel con il foglio Operazioni, ricostruisci il valore del portafoglio nel tempo. "
)


# ============================================================
# Helpers
# ============================================================
def normalize_text(s: str) -> str:
    s = str(s).strip().lower()
    replacements = {
        "à": "a", "è": "e", "é": "e", "ì": "i", "ò": "o", "ù": "u",
        "\xa0": " "
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    for ch in ["-", "/", "\\", ".", ",", ":", ";", "(", ")", "[", "]", "{", "}", "\n", "\t"]:
        s = s.replace(ch, " ")
    return " ".join(s.split())


def find_col(columns, candidates):
    norm_map = {normalize_text(c): c for c in columns}

    # match esatto normalizzato
    for candidate in candidates:
        key = normalize_text(candidate)
        if key in norm_map:
            return norm_map[key]

    # contains fallback
    for col in columns:
        ncol = normalize_text(col)
        if any(normalize_text(c) in ncol for c in candidates):
            return col

    return None


def parse_numeric(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()

    # Caso 1: 1.234,56
    mask_both = s.str.contains(r"\.") & s.str.contains(",")
    s.loc[mask_both] = (
        s.loc[mask_both]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    # Caso 2: 123,45
    mask_comma = ~s.str.contains(r"\.") & s.str.contains(",")
    s.loc[mask_comma] = s.loc[mask_comma].str.replace(",", ".", regex=False)

    return pd.to_numeric(s, errors="coerce")


def read_excel_safely(file_obj) -> bytes:
    """
    Restituisce bytes leggibili più volte sia per UploadedFile Streamlit
    sia per file locale Path.
    """
    if hasattr(file_obj, "read"):
        # UploadedFile o file-like
        data = file_obj.read()
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        return data
    else:
        # path-like
        return Path(file_obj).read_bytes()


def load_operations_from_excel(file_obj) -> pd.DataFrame:
    excel_bytes = read_excel_safely(file_obj)

    xls = pd.ExcelFile(BytesIO(excel_bytes), engine="openpyxl")
    sheet_name = None

    if "Operazioni" in xls.sheet_names:
        sheet_name = "Operazioni"
    else:
        # fallback: cerca un foglio con colonne compatibili
        for s in xls.sheet_names:
            tmp = pd.read_excel(BytesIO(excel_bytes), sheet_name=s, engine="openpyxl", nrows=20)
            c_ticker = find_col(tmp.columns, ["Ticker"])
            c_date = find_col(tmp.columns, ["Data", "Date"])
            c_qty = find_col(tmp.columns, ["Quantità", "Quantita", "Quantity", "Qta"])
            if c_ticker and c_date and c_qty:
                sheet_name = s
                break

    if sheet_name is None:
        raise ValueError(
            "Nessun foglio compatibile trovato. Serve un foglio con almeno: "
            "Ticker, Data, Quantità."
        )

    df = pd.read_excel(BytesIO(excel_bytes), sheet_name=sheet_name, engine="openpyxl")
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")

    col_id = find_col(df.columns, ["ID"])
    col_broker = find_col(df.columns, ["Intermediario"])
    col_ticker = find_col(df.columns, ["Ticker"])
    col_date = find_col(df.columns, ["Data", "Date"])
    col_qty = find_col(df.columns, ["Quantità", "Quantita", "Quantity", "Qta"])
    col_price = find_col(df.columns, ["Prezzo", "Price"])
    col_fee = find_col(df.columns, ["Spese euro", "SpeseEuro", "Commissioni", "Commissione", "Fees", "Fee"])
    col_tax = find_col(df.columns, ["Tassa"])
    col_name = find_col(df.columns, ["Nome"])
    col_type = find_col(df.columns, ["Tipo"])
    col_fx = find_col(df.columns, ["Cambio"])
    col_flusso_netto = find_col(df.columns, ["Flusso netto", "FlussoNetto"])
    col_pmc = find_col(df.columns, ["Prezzo medio s/carico", "Prezzo medio s_carico", "Prezzo medio"])
    col_area = find_col(df.columns, ["Area"])
    col_sector = find_col(df.columns, ["Settore"])
    col_issuer = find_col(df.columns, ["Emittente"])
    col_currency = find_col(df.columns, ["Valuta"])

    missing = [
        name for name, col in [
            ("Ticker", col_ticker),
            ("Data", col_date),
            ("Quantità", col_qty),
        ]
        if col is None
    ]
    if missing:
        raise ValueError(f"Colonne obbligatorie mancanti: {missing}")

    out = pd.DataFrame({
        "Ticker": df[col_ticker].astype(str).str.strip(),
        "Data": pd.to_datetime(df[col_date], dayfirst=True, errors="coerce"),
        "Quantita": parse_numeric(df[col_qty]),
    })

    out["ID"] = df[col_id] if col_id is not None else np.nan
    out["Intermediario"] = df[col_broker] if col_broker is not None else ""
    out["Prezzo"] = parse_numeric(df[col_price]) if col_price is not None else np.nan
    out["SpeseEuro"] = parse_numeric(df[col_fee]).fillna(0.0) if col_fee is not None else 0.0
    out["Tassa"] = parse_numeric(df[col_tax]).fillna(0.0) if col_tax is not None else 0.0
    out["Cambio"] = parse_numeric(df[col_fx]) if col_fx is not None else np.nan
    out["FlussoNetto"] = parse_numeric(df[col_flusso_netto]) if col_flusso_netto is not None else np.nan

    out["Nome"] = df[col_name] if col_name is not None else out["Ticker"]
    out["Tipo"] = df[col_type] if col_type is not None else ""
    out["Area"] = df[col_area] if col_area is not None else ""
    out["Settore"] = df[col_sector] if col_sector is not None else ""
    out["Emittente"] = df[col_issuer] if col_issuer is not None else ""
    out["Valuta"] = df[col_currency] if col_currency is not None else ""

    out = out.dropna(subset=["Ticker", "Data", "Quantita"])
    out = out[out["Ticker"] != ""]
    out = out.sort_values(["Data", "Ticker"]).reset_index(drop=True)

    # Chiave posizione: usa ID se presente, altrimenti fallback su Ticker|Intermediario
    out["PositionKey"] = np.where(
        out["ID"].notna(),
        out["ID"].astype(str).str.strip(),
        out["Ticker"].astype(str).str.strip() + "|" + out["Intermediario"].astype(str).str.strip()
    )

    return out
    
def load_dividends_from_excel(xls) -> pd.DataFrame:
    try:
        df = pd.read_excel(xls, sheet_name="DividendiCedole", engine="openpyxl").copy()
    except Exception:
        return pd.DataFrame(columns=["ID", "Data", "DividendoNetto", "Nome", "Valuta"])

    df.columns = [str(c).strip() for c in df.columns]

    col_id = find_col(df.columns, ["ID"])
    col_date = find_col(df.columns, ["Data"])
    col_div_net = find_col(df.columns, ["Dividendi euro Netti"])
    col_div_tot = find_col(df.columns, ["Dividendi totali euro"])
    col_name = find_col(df.columns, ["Nome"])
    col_currency = find_col(df.columns, ["Valuta"])

    out = pd.DataFrame()

    out["ID"] = df[col_id] if col_id is not None else np.nan
    out["Data"] = pd.to_datetime(df[col_date], errors="coerce", dayfirst=True)

    # preferisci il netto; fallback sul totale
    if col_div_net is not None:
        out["DividendoNetto"] = parse_numeric(df[col_div_net]).fillna(0.0)
    elif col_div_tot is not None:
        out["DividendoNetto"] = parse_numeric(df[col_div_tot]).fillna(0.0)
    else:
        out["DividendoNetto"] = 0.0

    out["Nome"] = df[col_name] if col_name is not None else ""
    out["Valuta"] = df[col_currency] if col_currency is not None else ""

    out = out[out["Data"].notna() & (out["DividendoNetto"] != 0)].copy()

    # se usi ID come chiave posizione
    out["PositionKey"] = np.where(
        out["ID"].notna(),
        out["ID"].astype(str).str.strip(),
        out["Nome"].astype(str).str.strip()
    )

    return out

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

    if raw is None or len(raw) == 0:
        return pd.DataFrame(), tickers

    closes = pd.DataFrame(index=raw.index)

    # Caso multiindex
    if isinstance(raw.columns, pd.MultiIndex):
        lvl0 = set(raw.columns.get_level_values(0))

        # Formato A: primo livello = ticker
        if all(t in lvl0 for t in tickers):
            for t in tickers:
                if "Close" in raw[t].columns:
                    closes[t] = raw[t]["Close"]
                elif "Adj Close" in raw[t].columns:
                    closes[t] = raw[t]["Adj Close"]

        else:
            # Formato B: primo livello = campo prezzo
            field = "Close" if "Close" in lvl0 else ("Adj Close" if "Adj Close" in lvl0 else None)
            if field is not None:
                sub = raw[field]
                for t in tickers:
                    if t in sub.columns:
                        closes[t] = sub[t]

    else:
        # caso singolo ticker semplice
        t = tickers[0]
        if "Close" in raw.columns:
            closes[t] = raw["Close"]
        elif "Adj Close" in raw.columns:
            closes[t] = raw["Adj Close"]

    closes = closes.sort_index().ffill()
    missing = [t for t in tickers if t not in closes.columns]

    return closes, missing

@st.cache_data(show_spinner=False)
def download_fx_series(currencies: list[str], start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    """
    Scarica il cambio giornaliero contro EUR.
    Convenzione proposta:
    - EURUSD=X  -> USD per 1 EUR
    - EURGBP=X  -> GBP per 1 EUR
    - EURCHF=X  -> CHF per 1 EUR

    Restituisce un DataFrame indicizzato per data con colonne = valute (USD, GBP, CHF, ...)
    e valori = quantità di valuta estera per 1 EUR.
    """
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

                # formato 1: primo livello = ticker
                if pair in lvl0:
                    if "Close" in raw[pair].columns:
                        fx[ccy] = raw[pair]["Close"]
                    elif "Adj Close" in raw[pair].columns:
                        fx[ccy] = raw[pair]["Adj Close"]
                else:
                    # formato 2: primo livello = campo prezzo
                    if "Close" in lvl0 and pair in raw["Close"].columns:
                        fx[ccy] = raw["Close"][pair]
                    elif "Adj Close" in lvl0 and pair in raw["Adj Close"].columns:
                        fx[ccy] = raw["Adj Close"][pair]
            else:
                # caso improbabile di un solo pair
                if "Close" in raw.columns:
                    fx[ccy] = raw["Close"]
                elif "Adj Close" in raw.columns:
                    fx[ccy] = raw["Adj Close"]
        except Exception:
            pass

    return fx.sort_index().ffill()

def convert_closes_to_eur(closes: pd.DataFrame, ops: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp):
    """
    Converte i prezzi giornalieri in EUR usando il Close giornaliero FX.
    - Se la valuta del ticker è EUR: lascia invariato
    - Se la valuta è USD/GBP/CHF/...:
        prezzo_eur = prezzo_in_valuta / (EUR<VALUTA>=X)

    Restituisce:
    - closes_eur: prezzi giornalieri convertiti in EUR
    - fx_rates: dataframe dei cambi giornalieri usati
    """
    closes_eur = closes.copy()

    # Mappa ticker -> valuta (ultima nota nelle operazioni)
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
        if ticker not in closes_eur.columns:
            continue

        if ccy == "EUR":
            continue

        if ccy in fx_rates.columns:
            fx_series = fx_rates[ccy].reindex(closes_eur.index).ffill()

            # proposta implementativa:
            # EURUSD=X = USD per 1 EUR
            # quindi USD -> EUR = USD / EURUSD
            closes_eur[ticker] = closes_eur[ticker] / fx_series

    return closes_eur, fx_rates

def get_snapshot_prices(tickers, closes):
    prices = {}

    for t in tickers:
        price = None

        # 1. fast_info
        try:
            info = yf.Ticker(t).fast_info
            price = info.get("lastPrice", None)
        except:
            pass

        # 2. history fallback
        if price is None or pd.isna(price):
            try:
                hist = yf.Ticker(t).history(period="5d")
                if not hist.empty:
                    price = hist["Close"].iloc[-1]
            except:
                pass

        # 3. fallback SICURO
        if price is None or pd.isna(price):
            if t in closes.columns:
                price = closes[t].dropna().iloc[-1]

        prices[t] = price

    return pd.Series(prices)

def build_holdings(ops: pd.DataFrame, idx: pd.DatetimeIndex) -> pd.DataFrame:
    keys = sorted(ops["PositionKey"].unique().tolist())
    holdings = pd.DataFrame(0.0, index=idx, columns=keys)

    daily_ops = ops.groupby(["Data", "PositionKey"], as_index=False)["Quantita"].sum()

    for k in keys:
        s = (
            daily_ops[daily_ops["PositionKey"] == k]
            .set_index("Data")["Quantita"]
            .sort_index()
        )
        holdings[k] = s.reindex(idx, fill_value=0).cumsum()

    return holdings


def build_portfolio(ops: pd.DataFrame, closes: pd.DataFrame, dividends: pd.DataFrame | None = None):
    # ---------------------------------------------------
    # 1) Tieni solo i ticker per cui hai prezzi Yahoo
    # ---------------------------------------------------
    valid_tickers = [t for t in ops["Ticker"].unique() if t in closes.columns]
    ops = ops[ops["Ticker"].isin(valid_tickers)].copy()

    if ops.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    idx = closes.index

    # ---------------------------------------------------
    # 2) Holdings per PositionKey
    # ---------------------------------------------------
    holdings = build_holdings(ops, idx)

    # ---------------------------------------------------
    # 3) Prezzi per ticker -> conversione EUR giornaliera
    # ---------------------------------------------------
    closes_ticker = closes[valid_tickers].reindex(idx).ffill()

    start_date = ops["Data"].min().normalize()
    end_date = pd.Timestamp.today().normalize()

    # assume che convert_closes_to_eur lavori su colonne=ticker
    closes_eur_ticker, fx_rates = convert_closes_to_eur(
        closes_ticker,
        ops,
        start_date,
        end_date
    )

    # ---------------------------------------------------
    # 4) Espandi i prezzi ticker sulle posizioni
    #    (una posizione = un PositionKey)
    # ---------------------------------------------------
    position_to_ticker = (
        ops.groupby("PositionKey")["Ticker"]
        .last()
    )

    position_closes_eur = pd.DataFrame(index=idx)

    for pos_key in holdings.columns:
        t = position_to_ticker.loc[pos_key]
        if t in closes_eur_ticker.columns:
            position_closes_eur[pos_key] = closes_eur_ticker[t]

    # ---------------------------------------------------
    # 5) Valore giornaliero per posizione / portafoglio
    # ---------------------------------------------------
    position_values = holdings * position_closes_eur
    total_value = position_values.sum(axis=1).rename("Valore portafoglio")

    # ---------------------------------------------------
    # 6) Cashflow storico corretto
    # ---------------------------------------------------
    ops_cf = ops.copy()
    st.write("Columns:", ops_cf.columns)
    ops_cf["Prezzo"] = ops_cf["Prezzo"].fillna(0.0)
    ops_cf["SpeseEuro"] = ops_cf["SpeseEuro"].fillna(0.0)
    ops_cf["Cambio"] = ops_cf["Cambio"].fillna(1.0)

    # Se esiste FlussoNetto lo uso (più fedele al tuo Excel)
    # altrimenti ricostruisco
    ops_cf["Cashflow"] = np.where(
        ops_cf["FlussoNetto"].notna(),
        ops_cf["FlussoNetto"],
        -(ops_cf["Quantita"] * ops_cf["Prezzo"] * ops_cf["Cambio"]) - ops_cf["SpeseEuro"]
    )
    # ---------------------------------------------------
    # Dividendi/Cedole netti giornalieri
    # ---------------------------------------------------
    if dividends is None or dividends.empty:
        daily_dividends = pd.Series(0.0, index=idx, name="Dividendi netti")
    else:
        daily_dividends = (
            dividends.groupby("Data")["DividendoNetto"]
            .sum()
            .reindex(idx, fill_value=0.0)
            .rename("Dividendi netti")
        )

    # ---------------------------------------------------
    # Realizzato giornaliero = profitto da vendite + dividendi
    # ---------------------------------------------------
    sell_ops = ops_cf.loc[ops_cf["Quantita"] < 0].copy()

    # profitto netto realizzato per ogni vendita:
    # incasso netto vendita - costo storico della quantità venduta

    sell_ops["RealizedTradePL"] = (
        sell_ops["FlussoNetto"]
        - (sell_ops["Quantita"].abs() * sell_ops[col_pmc])
    )


    realized_from_trades = (
        sell_ops.groupby("Data")["RealizedTradePL"]
        .sum()
        .reindex(idx, fill_value=0.0)
    )

    realized_daily = realized_from_trades.add(daily_dividends, fill_value=0.0)

    pl_realizzato = realized_daily.cumsum().rename("P/L realizzato")


    # cashflow totale giornaliero
    daily_cf_total = (
        ops_cf.groupby("Data")["Cashflow"]
        .sum()
        .reindex(idx, fill_value=0.0)
    )

    # capitale investito cumulato
    invested = (
        daily_cf_total
        .cumsum()
        .rename("Capitale investito")
    )

    # ---------------------------------------------------
    # 7) Cashflow giornaliero per posizione
    # ---------------------------------------------------
    daily_cf_positions = (
        ops_cf.groupby(["Data", "PositionKey"])["Cashflow"]
        .sum()
        .unstack(fill_value=0.0)
        .reindex(index=idx, columns=holdings.columns, fill_value=0.0)
    )

    # ---------------------------------------------------
    # 8) P/L giornaliero corretto
    #    (diff valori + cashflow del giorno)
    # ---------------------------------------------------
    daily_pl_positions = (
        position_values.diff().fillna(0.0)
        .add(daily_cf_positions, fill_value=0.0)
    )

    daily_pl = daily_pl_positions.sum(axis=1).rename("P/L Giornaliero")
    
    # ✅ NUOVO: P/L Giornaliero %
    daily_pl_pct = (daily_pl / total_value.shift(1)).rename("P/L Giornaliero %")

    pnl = (total_value + invested).rename("P/L totale")

    ts = pd.concat([total_value, invested, pnl, daily_pl, daily_pl_pct, daily_dividends, pl_realizzato],axis=1)
    
    # =========================
    #     DEBUG P/L mismatch
    # =========================
    # debug = pd.DataFrame({
    #     "P/L totale": pnl,
    #     "Delta P/L totale": pnl.diff(),
    #     "P/L giornaliero": daily_pl,
    # })

    # st.write("DEBUG confronto P/L:")
    # st.write(debug.tail(5))


    # ---------------------------------------------------
    # 9) Snapshot finale per posizione
    # ---------------------------------------------------
    last_qty = holdings.iloc[-1]
    last_close_eur = position_closes_eur.iloc[-1]
    last_daily_pl = daily_pl_positions.iloc[-1]

    # Metadati per PositionKey
    meta = (
        ops.sort_values("Data")
        .groupby("PositionKey")
        .agg({
            "ID": "last" if "ID" in ops.columns else "first",
            "Ticker": "last",
            "Intermediario": "last" if "Intermediario" in ops.columns else "first",
            "Nome": "last",
            "Tipo": "last",
            "Area": "last",
            "Settore": "last",
            "Emittente": "last",
            "Valuta": "last",
            "Tassa": "last",   # percentuale
        })
    )

    # ---------------------------------------------------
    # 10) Costo medio stimato per posizione
    # ---------------------------------------------------
    cost_df = ops.copy()
    cost_df["CostoFirmato"] = (
        (cost_df["Quantita"] * cost_df["Prezzo"].fillna(0.0))
        + cost_df["SpeseEuro"].fillna(0.0)
    )

    agg_cost = cost_df.groupby("PositionKey").agg(
        NetQty=("Quantita", "sum"),
        GrossCost=("CostoFirmato", "sum")
    )

    # ---------------------------------------------------
    # 11) Costruisci current per posizione
    # ---------------------------------------------------
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

    # Tassa è già una percentuale per posizione
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

    if dividends is not None and not dividends.empty:
        dividends_by_position = (
            dividends.groupby("PositionKey")["DividendoNetto"]
            .sum()
            .rename("Dividendi Netti Incassati")
        )
        current = current.join(dividends_by_position, how="left")
        current["Dividendi Netti Incassati"] = current["Dividendi Netti Incassati"].fillna(0.0)
    else:
        current["Dividendi Netti Incassati"] = 0.0
        
    st.write("Dividends keys:", dividends["PositionKey"].unique())
    st.write("Current keys:", current["PositionKey"].unique())

    # Tieni solo posizioni aperte
    current = current[current["Quantita"] != 0].sort_values("Valore", ascending=False)

    # exposure/tabella finale
    exposure = current.reset_index().rename(columns={"index": "PositionKey"})

    return ts, current, holdings, exposure


def fmt_eur(x):
    try:
        return f"€ {x:,.2f}"
    except Exception:
        return "-"


def fmt_pct(x):
    try:
        return f"{x:.2%}"
    except Exception:
        return "-"


# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.header("Sorgente dati")
    uploaded_file = st.file_uploader("Carica il file Excel", type=["xlsx"])

    use_local_demo = st.checkbox("Usa file locale demo se presente", value=True)

    st.markdown("---")
    
    if st.button("🔄 Aggiorna prezzi"):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}")
    
    st.header("Opzioni")
    benchmark = st.text_input("Ticker benchmark Yahoo (opzionale)", value="CSSPX.MI")
    show_benchmark = st.checkbox("Mostra benchmark normalizzato", value=True)

    default_start = datetime(2026, 3, 1)
    min_filter_date = st.date_input("Data minima", value=default_start)

    st.markdown("---")
    st.caption(
        "Suggerimento: per una app pubblica, usa l'upload del file. "
        "È il modo più robusto su Streamlit Cloud."
    )


# ============================================================
# Input source
# ============================================================
file_source = None
file_label = None

if uploaded_file is not None:
    file_source = uploaded_file
    file_label = uploaded_file.name
elif use_local_demo:
    candidates = [
        Path("portafoglio_query_yf_ETF.xlsx"),
        Path("[portafoglio_query_yf_ETF.xlsx](https://onedrive.live.com/personal/f4457315c1bde87e/_layouts/15/doc.aspx?resid=599cff68-dc19-4797-8899-3344181a781b&cid=f4457315c1bde87e&EntityRepresentationId=8927e0d4-7d44-4e82-925a-8dcab7fcc8b9)"),
    ]
    for c in candidates:
        if c.exists():
            file_source = c
            file_label = c.name
            break

if file_source is None:
    st.info("Carica un file Excel per iniziare.")
    st.stop()


# ============================================================
# Load operations
# ============================================================
try:
    ops = load_operations_from_excel(file_source)
    dividends = load_dividends_from_excel(file_source)
except Exception as e:
    st.error(f"Errore nel caricamento del file: {e}")
    st.stop()

ops = ops[ops["Data"] >= pd.Timestamp(min_filter_date)]
if ops.empty:
    st.warning("Nessuna operazione disponibile dopo la data minima selezionata.")
    st.stop()

st.success(f"File caricato: {file_label}")

with st.expander("Anteprima operazioni", expanded=False):
    st.dataframe(ops, use_container_width=True)


# ============================================================
# Price download
# ============================================================
start_date = ops["Data"].min().normalize()
end_date = pd.Timestamp.today().normalize()

closes, missing = download_close_prices(
    sorted(ops["Ticker"].unique().tolist()),
    start_date,
    end_date
)

if closes.empty:
    st.error("Non sono riuscito a scaricare i prezzi da Yahoo Finance.")
    st.stop()

if missing:
    st.warning("Ticker senza prezzi scaricati: " + ", ".join(missing))


# ============================================================
# Portfolio computation
# ============================================================
series, current, holdings, exposure = build_portfolio(ops, closes, dividends)

st.write(series[["Dividendi netti", "P/L realizzato"]].tail(20))

# debug info
# st.write("Valore portafoglio finale:", series["Valore portafoglio"].iloc[-1])
# st.write("Capitale investito finale:", series["Capitale investito"].iloc[-1])
# st.write("P/L finale:", series["P/L totale"].iloc[-1])


if series.empty:
    st.error("Non è stato possibile costruire il portafoglio con i dati disponibili.")
    st.stop()


# ============================================================
# Benchmark
# ============================================================
bench_norm = None
if show_benchmark and benchmark.strip():
    bench_df, bench_missing = download_close_prices(
        [benchmark.strip()],
        start_date,
        end_date
    )
    if not bench_df.empty and benchmark.strip() in bench_df.columns:
        b = bench_df[benchmark.strip()].dropna()
        if not b.empty and b.iloc[0] != 0:
            bench_norm = abs(series["Capitale investito"].iloc[-1]) * (b / b.iloc[0])


# ============================================================
# KPIs
# ============================================================
latest_value = float(series["Valore portafoglio"].iloc[-1])
latest_invested = float(series["Capitale investito"].iloc[-1])
latest_pnl = float(series["P/L totale"].iloc[-1])
latest_daily_pl = float(series["P/L Giornaliero"].iloc[-1])
latest_daily_pl_pct = float(series["P/L Giornaliero %"].iloc[-1])
latest_pnl_pct = latest_pnl / abs(latest_invested) if latest_invested != 0 else np.nan

latest_realized = float(series["P/L realizzato"].iloc[-1])
latest_dividends = float(series["Dividendi netti"].sum())
latest_realized_pct = latest_realized / latest_invested if latest_invested != 0 else np.nan


k1, k2, k3, k4 = st.columns(4)
k1.metric("Valore portafoglio", fmt_eur(latest_value))
k2.metric("Capitale investito", fmt_eur(latest_invested))
k3.metric("Posizioni aperte", len(current))
k4.metric("Dividendi netti", fmt_eur(latest_dividends))

k5, k6, k7  = st.columns(3)
k5.metric("P/L totale", fmt_eur(latest_pnl), delta=fmt_pct(latest_pnl_pct), delta_color="normal" if pd.notna(latest_pnl_pct) else None)
k6.metric("P/L Giornaliero",fmt_eur(latest_daily_pl),delta=fmt_pct(latest_daily_pl_pct),delta_color="normal" if pd.notna(latest_daily_pl_pct) else None)
k7.metric("P/L realizzato", fmt_eur(latest_realized),delta=fmt_pct(latest_realized_pct))

# ============================================================
# Main chart
# ============================================================
st.subheader("Andamento del portafoglio nel tempo")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=series.index,
    y=series["Valore portafoglio"],
    mode="lines",
    name="Valore portafoglio"
))
fig.add_trace(go.Scatter(
    x=series.index,
    y=series["Capitale investito"],
    mode="lines",
    name="Capitale investito"
))
fig.add_trace(go.Scatter(
    x=series.index,
    y=series["P/L totale"],
    mode="lines",
    name="P/L totale",
    yaxis="y2"
))

if bench_norm is not None:
    fig.add_trace(go.Scatter(
        x=bench_norm.index,
        y=bench_norm.values,
        mode="lines",
        name=f"Benchmark normalizzato: {benchmark.strip()}"
    ))

fig.update_layout(
    height=540,
    xaxis_title="Data",
    yaxis_title="Euro",
    yaxis2=dict(
        title="P/L",
        overlaying="y",
        side="right",
        showgrid=False
    ),
    legend=dict(orientation="h"),
    margin=dict(l=20, r=20, t=20, b=20)
)

st.plotly_chart(fig, use_container_width=True)


# ============================================================
# Tabs
# ============================================================
tab_pos, tab_exp, tab_ops, tab_dl = st.tabs(
    ["Posizioni", "Esposizione", "Operazioni", "Download"]
)

with tab_pos:
    st.subheader("Posizioni correnti")
    current_view = current.reset_index().rename(columns={"index": "PositionKey"})

    ordered_cols = [
        "Ticker", "Intermediario", "Nome", "Tipo", "Area", "Settore", "Emittente", "Valuta",
        "Quantita", "Prezzo Attuale", "Valore","Dividendi Netti Incassati",
        "Costo Medio Stimato", "Costo Totale Stimato", "P/L", "P/L %", "P/L Netto Stimato","P/L Giornaliero","P/L Giornaliero %"
    ]
    ordered_cols = [c for c in ordered_cols if c in current_view.columns]

def color_pl(val):
    if pd.isna(val):
        return ""
    elif val > 0:
        return "color: #00ff00; font-weight: bold"
    elif val < 0:
        return "color: #ff4d4d; font-weight: bold"
    else:
        return ""

def style_pl_column(col):
    if col.name in ["P/L", "P/L %", "P/L Netto Stimato","P/L Giornaliero","P/L Giornaliero %"]:
        return [color_pl(v) for v in col]
    else:
        return [""] * len(col)  # ✅ importante!

st.dataframe(
    current_view[ordered_cols]
    .style
    .format({
        "Prezzo Attuale": "{:,.4f}",
        "Valore": "€ {:,.2f}",
        "Dividendi Netti Incassati": "€ {:,.2f}",
        "Costo Medio Stimato": "{:,.4f}",
        "Costo Totale Stimato": "€ {:,.2f}",
        "P/L": "€ {:,.2f}",
        "P/L %": "{:.2%}",
        "P/L Netto Stimato": "€ {:,.2f}",
        "P/L Giornaliero": "€ {:,.2f}",
        "P/L Giornaliero %": "{:.2%}",
    })
    .apply(style_pl_column, axis=0),
    use_container_width=True
)

with tab_exp:
    st.subheader("Allocazione")
    pie = px.pie(exposure, names="Ticker", values="Valore", hole=0.45)
    pie.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(pie, use_container_width=True)

    c1, c2 = st.columns(2)

    if "Area" in exposure.columns and exposure["Area"].astype(str).str.strip().any():
        area_df = (
            exposure.groupby("Area", dropna=False)["Valore"]
            .sum()
            .reset_index()
            .sort_values("Valore", ascending=False)
        )
        c1.plotly_chart(
            px.bar(area_df, x="Area", y="Valore", title="Per area"),
            use_container_width=True
        )

    if "Tipo" in exposure.columns and exposure["Tipo"].astype(str).str.strip().any():
        tipo_df = (
            exposure.groupby("Tipo", dropna=False)["Valore"]
            .sum()
            .reset_index()
            .sort_values("Valore", ascending=False)
        )
        c2.plotly_chart(
            px.bar(tipo_df, x="Tipo", y="Valore", title="Per tipo"),
            use_container_width=True
        )

with tab_ops:
    st.subheader("Operazioni")
    all_tickers = ["Tutti"] + sorted(ops["Ticker"].unique().tolist())
    selected_ticker = st.selectbox("Filtra per ticker", all_tickers)

    show_ops = ops if selected_ticker == "Tutti" else ops[ops["Ticker"] == selected_ticker]
    st.dataframe(show_ops, use_container_width=True)

with tab_dl:
    st.subheader("Download risultati")

    ts_csv = (
        series.reset_index()
        .rename(columns={"index": "Data"})
        .to_csv(index=False)
        .encode("utf-8")
    )
    current_csv = (
        current.reset_index()
        .rename(columns={"index": "Ticker"})
        .to_csv(index=False)
        .encode("utf-8")
    )
    ops_csv = ops.to_csv(index=False).encode("utf-8")

    d1, d2, d3 = st.columns(3)
    d1.download_button(
        "Scarica serie storica CSV",
        ts_csv,
        file_name="serie_storica_portafoglio.csv",
        mime="text/csv"
    )
    d2.download_button(
        "Scarica posizioni correnti CSV",
        current_csv,
        file_name="posizioni_correnti.csv",
        mime="text/csv"
    )
    d3.download_button(
        "Scarica operazioni CSV",
        ops_csv,
        file_name="operazioni_portafoglio.csv",
        mime="text/csv"
    )


# ============================================================
# Footer instructions
# ============================================================
st.markdown("---")

st.markdown("### 📈 Portfolio Tracker")
st.caption("Aggiornamento in tempo reale dei prezzi")

