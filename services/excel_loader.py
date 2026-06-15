from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd


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

    for candidate in candidates:
        key = normalize_text(candidate)
        if key in norm_map:
            return norm_map[key]

    for col in columns:
        ncol = normalize_text(col)
        if any(normalize_text(c) in ncol for c in candidates):
            return col

    return None


def parse_numeric(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()

    mask_both = s.str.contains(r"\.") & s.str.contains(",")
    s.loc[mask_both] = (
        s.loc[mask_both]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    mask_comma = ~s.str.contains(r"\.") & s.str.contains(",")
    s.loc[mask_comma] = s.loc[mask_comma].str.replace(",", ".", regex=False)

    return pd.to_numeric(s, errors="coerce")


def read_excel_safely(file_obj) -> bytes:
    if hasattr(file_obj, "read"):
        data = file_obj.read()
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        return data
    return Path(file_obj).read_bytes()


def find_standard_col(df: pd.DataFrame, col_name: str):
    """
    Trova la colonna nel dataframe usando gli alias definiti nello schema.
    """
    from services.schema import COLUMN_ALIASES
    return find_col(df.columns, COLUMN_ALIASES[col_name])


def load_operations_from_excel(file_obj) -> pd.DataFrame:
    excel_bytes = read_excel_safely(file_obj)
    xls = pd.ExcelFile(BytesIO(excel_bytes), engine="openpyxl")

    sheet_name = None

    if "Operazioni" in xls.sheet_names:
        sheet_name = "Operazioni"
    else:
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
            "Nessun foglio compatibile trovato. Serve un foglio con almeno: Ticker, Data, Quantità."
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
    valore = (out["Quantita"] * out["Prezzo"].fillna(0.0) * out["Cambio"].fillna(1.0))

    # ✅ fallback se FlussoNetto non c'è (file demo)
    flusso_base = - valore - out["SpeseEuro"].fillna(0.0)
    
    # ✅ se FlussoNetto esiste → usa quello (file reale)
    if col_flusso_netto is not None:
        out["FlussoNetto"] = parse_numeric(df[col_flusso_netto])
    else:
        out["FlussoNetto"] = flusso_base

    out["Prezzo medio s/carico"] = parse_numeric(df[col_pmc]) if col_pmc is not None else np.nan

    out["Nome"] = df[col_name] if col_name is not None else out["Ticker"]
    out["Tipo"] = df[col_type] if col_type is not None else ""
    out["Area"] = df[col_area] if col_area is not None else ""
    out["Settore"] = df[col_sector] if col_sector is not None else ""
    out["Emittente"] = df[col_issuer] if col_issuer is not None else ""
    out["Valuta"] = df[col_currency] if col_currency is not None else ""

    out = out.dropna(subset=["Ticker", "Data", "Quantita"])
    out = out[out["Ticker"] != ""]
    out = out.sort_values(["Data", "Ticker"]).reset_index(drop=True)

    out["PositionKey"] = np.where(
        out["ID"].notna(),
        out["ID"].astype(str).str.strip(),
        out["Ticker"].astype(str).str.strip() + "|" + out["Intermediario"].astype(str).str.strip()
    )

    return out


def load_dividends_from_excel(file_obj) -> pd.DataFrame:
    excel_bytes = read_excel_safely(file_obj)

    try:
        df = pd.read_excel(BytesIO(excel_bytes), sheet_name="DividendiCedole", engine="openpyxl").copy()
    except Exception:
        return pd.DataFrame(columns=["ID", "Data", "DividendoNetto", "Nome", "Valuta", "PositionKey"])

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

    if col_div_net is not None:
        out["DividendoNetto"] = parse_numeric(df[col_div_net]).fillna(0.0)
    elif col_div_tot is not None:
        out["DividendoNetto"] = parse_numeric(df[col_div_tot]).fillna(0.0)
    else:
        out["DividendoNetto"] = 0.0

    out["Nome"] = df[col_name] if col_name is not None else ""
    out["Valuta"] = df[col_currency] if col_currency is not None else ""

    out = out[out["Data"].notna() & (out["DividendoNetto"] != 0)].copy()

    out["PositionKey"] = np.where(
        out["ID"].notna(),
        out["ID"].astype(str).str.strip(),
        out["Nome"].astype(str).str.strip()
    )

    return out
