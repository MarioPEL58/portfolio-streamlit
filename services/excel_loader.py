from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd

from services.schema import (
    COLUMN_ALIASES,
    DIVIDEND_ALIASES,
    SHEET_ALIASES,
    REQUIRED_OPERATION_COLUMNS,
    REQUIRED_DIVIDEND_COLUMNS,
)


# =========================================================
# Utilities
# =========================================================

def normalize_text(s: str) -> str:
    s = str(s).strip().lower()

    replacements = {
        "à": "a",
        "è": "e",
        "é": "e",
        "ì": "i",
        "ò": "o",
        "ù": "u",
        "\xa0": " ",
    }

    for old, new in replacements.items():
        s = s.replace(old, new)

    for ch in ["-", "/", "\\", ".", ",", ":", ";", "(", ")", "[", "]", "{", "}", "\n", "\t"]:
        s = s.replace(ch, " ")

    return " ".join(s.split())


def read_excel_safely(file_obj) -> bytes:
    if hasattr(file_obj, "read"):
        data = file_obj.read()
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        return data
    return Path(file_obj).read_bytes()


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


# =========================================================
# Column / Sheet detection
# =========================================================

def find_col(columns, candidates):
    norm_map = {normalize_text(c): c for c in columns}

    # match esatto
    for candidate in candidates:
        key = normalize_text(candidate)
        if key in norm_map:
            return norm_map[key]

    # match parziale
    for col in columns:
        ncol = normalize_text(col)
        if any(normalize_text(c) in ncol for c in candidates):
            return col

    return None


def find_sheet_name(sheet_names, candidates):
    norm_map = {normalize_text(s): s for s in sheet_names}

    # match esatto
    for candidate in candidates:
        key = normalize_text(candidate)
        if key in norm_map:
            return norm_map[key]

    # match parziale
    for sheet in sheet_names:
        nsheet = normalize_text(sheet)
        if any(normalize_text(c) in nsheet for c in candidates):
            return sheet

    return None


def find_standard_col(df: pd.DataFrame, col_name: str, aliases_dict: dict | None = None):
    aliases_dict = aliases_dict or COLUMN_ALIASES
    aliases = aliases_dict.get(col_name, [])
    return find_col(df.columns, aliases)


def map_columns(df: pd.DataFrame, aliases_dict: dict) -> dict:
    return {
        std_name: find_standard_col(df, std_name, aliases_dict)
        for std_name in aliases_dict.keys()
    }


def missing_required(mapped_cols: dict, required_cols: list[str]) -> list[str]:
    return [col for col in required_cols if mapped_cols.get(col) is None]


# =========================================================
# Excel structure detection
# =========================================================

def detect_excel_structure(file_obj) -> dict:
    excel_bytes = read_excel_safely(file_obj)
    xls = pd.ExcelFile(BytesIO(excel_bytes), engine="openpyxl")

    # -------------------------
    # Operazioni
    # -------------------------
    operations_sheet = find_sheet_name(
        xls.sheet_names,
        SHEET_ALIASES["Operazioni"]
    )

    operations_columns = {}

    if operations_sheet is not None:
        tmp = pd.read_excel(
            BytesIO(excel_bytes),
            sheet_name=operations_sheet,
            engine="openpyxl",
            nrows=30
        )
        tmp = tmp.dropna(axis=0, how="all").dropna(axis=1, how="all")
        operations_columns = map_columns(tmp, COLUMN_ALIASES)

    # fallback: trova il primo foglio compatibile dalle colonne
    if operations_sheet is None:
        for s in xls.sheet_names:
            tmp = pd.read_excel(
                BytesIO(excel_bytes),
                sheet_name=s,
                engine="openpyxl",
                nrows=30
            )
            tmp = tmp.dropna(axis=0, how="all").dropna(axis=1, how="all")
            mapped = map_columns(tmp, COLUMN_ALIASES)
            missing = missing_required(mapped, REQUIRED_OPERATION_COLUMNS)

            if not missing:
                operations_sheet = s
                operations_columns = mapped
                break

    operations_missing = (
        missing_required(operations_columns, REQUIRED_OPERATION_COLUMNS)
        if operations_sheet is not None
        else REQUIRED_OPERATION_COLUMNS.copy()
    )

    # -------------------------
    # Dividendi / Cedole
    # -------------------------
    dividends_sheet = find_sheet_name(
        xls.sheet_names,
        SHEET_ALIASES["DividendiCedole"]
    )

    dividends_columns = {}

    if dividends_sheet is not None:
        tmp = pd.read_excel(
            BytesIO(excel_bytes),
            sheet_name=dividends_sheet,
            engine="openpyxl",
            nrows=30
        )
        tmp = tmp.dropna(axis=0, how="all").dropna(axis=1, how="all")
        dividends_columns = map_columns(tmp, DIVIDEND_ALIASES)

    dividends_missing = (
        missing_required(dividends_columns, REQUIRED_DIVIDEND_COLUMNS)
        if dividends_sheet is not None
        else REQUIRED_DIVIDEND_COLUMNS.copy()
    )
    # -------------------------
    # Start (snapshot iniziale)
    # -------------------------
    start_sheet = find_sheet_name(
        xls.sheet_names,
        ["start"]
    )
    
    start_is_valid = False
    
    if start_sheet is not None:
        tmp = pd.read_excel(
            BytesIO(excel_bytes),
            sheet_name=start_sheet,
            engine="openpyxl",
            nrows=30
        )
    
        tmp = tmp.dropna(axis=0, how="all").dropna(axis=1, how="all")
        tmp.columns = tmp.columns.str.strip()
    
        required_start_cols = ["Data", "Ticker", "Quantita", "Prezzo"]

    start_is_valid = all(col in tmp.columns for col in required_start_cols)
    return {
        "sheet_names": xls.sheet_names,
        "operations": {
            "sheet_name": operations_sheet,
            "columns": operations_columns,
            "missing_required": operations_missing,
            "is_valid": operations_sheet is not None and len(operations_missing) == 0,
        },
        "dividends": {
            "sheet_name": dividends_sheet,
            "columns": dividends_columns,
            "missing_required": dividends_missing,
            "is_valid": dividends_sheet is not None and len(dividends_missing) == 0,
        },
        "start": {
            "sheet_name": start_sheet,
            "is_valid": start_is_valid,
        },
    }


# =========================================================
# Load operations
# =========================================================

def load_operations_from_excel(file_obj) -> pd.DataFrame:
    structure = detect_excel_structure(file_obj)

    if not structure["operations"]["is_valid"]:
        missing = structure["operations"]["missing_required"]
        raise ValueError(
            f"Nessun foglio compatibile trovato. Colonne obbligatorie mancanti: {missing}"
        )

    excel_bytes = read_excel_safely(file_obj)
    sheet_name = structure["operations"]["sheet_name"]
    cols = structure["operations"]["columns"]

    df = pd.read_excel(BytesIO(excel_bytes), sheet_name=sheet_name, engine="openpyxl")
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")

    out = pd.DataFrame({
        "Ticker": df[cols["Ticker"]].astype(str).str.strip(),
        "Data": pd.to_datetime(df[cols["Data"]], dayfirst=True, errors="coerce"),
        "Quantita": parse_numeric(df[cols["Quantita"]]),
    })

    out["ID"] = df[cols["ID"]] if cols.get("ID") is not None else np.nan
    out["Intermediario"] = df[cols["Intermediario"]] if cols.get("Intermediario") is not None else ""
    out["Prezzo"] = parse_numeric(df[cols["Prezzo"]]) if cols.get("Prezzo") is not None else np.nan
    out["SpeseEuro"] = (
        parse_numeric(df[cols["SpeseEuro"]]).fillna(0.0)
        if cols.get("SpeseEuro") is not None else 0.0
    )
    out["Tassa"] = (
        parse_numeric(df[cols["Tassa"]]).fillna(0.0)
        if cols.get("Tassa") is not None else 0.0
    )
    out["Cambio"] = (
        parse_numeric(df[cols["Cambio"]])
        if cols.get("Cambio") is not None else np.nan
    )

    valore = out["Quantita"] * out["Prezzo"].fillna(0.0) * out["Cambio"].fillna(1.0)
    flusso_base = -valore - out["SpeseEuro"].fillna(0.0)

    if cols.get("FlussoNetto") is not None:
        out["FlussoNetto"] = parse_numeric(df[cols["FlussoNetto"]])
    else:
        out["FlussoNetto"] = flusso_base

    out["Prezzo medio s/carico"] = (
        parse_numeric(df[cols["Prezzo medio s/carico"]])
        if cols.get("Prezzo medio s/carico") is not None else np.nan
    )

    out["Nome"] = df[cols["Nome"]] if cols.get("Nome") is not None else out["Ticker"]
    out["Tipo"] = df[cols["Tipo"]] if cols.get("Tipo") is not None else ""
    out["Area"] = df[cols["Area"]] if cols.get("Area") is not None else ""
    out["Settore"] = df[cols["Settore"]] if cols.get("Settore") is not None else ""
    out["Emittente"] = df[cols["Emittente"]] if cols.get("Emittente") is not None else ""
    out["Valuta"] = df[cols["Valuta"]] if cols.get("Valuta") is not None else ""

    out = out.dropna(subset=["Ticker", "Data", "Quantita"])
    out = out[out["Ticker"] != ""]
    out = out.sort_values(["Data", "Ticker"]).reset_index(drop=True)

    out["PositionKey"] = np.where(
        out["ID"].notna(),
        out["ID"].astype(str).str.strip(),
        out["Ticker"].astype(str).str.strip() + "|" + out["Intermediario"].astype(str).str.strip()
    )

    return out


# =========================================================
# Load dividends
# =========================================================

def load_dividends_from_excel(file_obj) -> pd.DataFrame:
    structure = detect_excel_structure(file_obj)

    if not structure["dividends"]["is_valid"]:
        return pd.DataFrame(
            columns=["ID", "Data", "DividendoNetto", "Nome", "Valuta", "PositionKey"]
        )

    excel_bytes = read_excel_safely(file_obj)
    sheet_name = structure["dividends"]["sheet_name"]
    cols = structure["dividends"]["columns"]

    df = pd.read_excel(BytesIO(excel_bytes), sheet_name=sheet_name, engine="openpyxl").copy()
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")

    out = pd.DataFrame()
    out["ID"] = df[cols["ID"]] if cols.get("ID") is not None else np.nan
    out["Data"] = pd.to_datetime(df[cols["Data"]], errors="coerce", dayfirst=True)

    if cols.get("DividendoNetto") is not None:
        out["DividendoNetto"] = parse_numeric(df[cols["DividendoNetto"]]).fillna(0.0)
    elif cols.get("DividendoTotale") is not None:
        out["DividendoNetto"] = parse_numeric(df[cols["DividendoTotale"]]).fillna(0.0)
    else:
        out["DividendoNetto"] = 0.0

    out["Nome"] = df[cols["Nome"]] if cols.get("Nome") is not None else ""
    out["Valuta"] = df[cols["Valuta"]] if cols.get("Valuta") is not None else ""

    out = out[out["Data"].notna() & (out["DividendoNetto"] != 0)].copy()

    out["PositionKey"] = np.where(
        out["ID"].notna(),
        out["ID"].astype(str).str.strip(),
        out["Nome"].astype(str).str.strip()
    )

    return out
    
def load_start_from_excel(file_obj) -> pd.DataFrame:
    excel_bytes = read_excel_safely(file_obj)
    xls = pd.ExcelFile(BytesIO(excel_bytes), engine="openpyxl")

    # ✅ trova foglio Start
    start_sheet = find_sheet_name(xls.sheet_names, ["start"])

    # ✅ fallback vuoto (importante per non rompere app)
    if start_sheet is None:
        return pd.DataFrame(columns=[
            "Ticker", "Data", "Quantita", "Prezzo",
            "FlussoNetto", "ID", "Intermediario",
            "SpeseEuro", "Tassa", "Cambio",
            "Nome", "Tipo", "Area", "Settore",
            "Emittente", "Valuta", "PositionKey"
        ])

    df = pd.read_excel(BytesIO(excel_bytes), sheet_name=start_sheet, engine="openpyxl")
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")

    # ✅ normalizza colonne
    df.columns = df.columns.str.strip()

    # ✅ VALIDAZIONE MINIMA
    required = ["Data", "Ticker", "Quantita", "Prezzo"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(f"Foglio Start mancante colonne obbligatorie: {missing}")

    # =========================
    # ✅ COSTRUZIONE OUTPUT
    # =========================
    out = pd.DataFrame()

    out["Ticker"] = df["Ticker"].astype(str).str.strip()
    out["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    out["Quantita"] = parse_numeric(df["Quantita"])
    out["Prezzo"] = parse_numeric(df["Prezzo"])

    # ✅ Flusso: se non presente lo calcolo
    if "FlussoNetto" in df.columns:
        out["FlussoNetto"] = parse_numeric(df["FlussoNetto"])
    else:
        out["FlussoNetto"] = - out["Quantita"] * out["Prezzo"]

    # =========================
    # ✅ CAMPI STANDARD
    # =========================
    out["ID"] = df["ID"] if "ID" in df.columns else np.nan
    out["Intermediario"] = df["Intermediario"] if "Intermediario" in df.columns else ""

    out["SpeseEuro"] = 0.0
    out["Tassa"] = 0.0
    out["Cambio"] = 1.0

    out["Nome"] = df["Nome"] if "Nome" in df.columns else out["Ticker"]
    out["Tipo"] = "INIT"   # ✅ distinguibile
    out["Area"] = ""
    out["Settore"] = ""
    out["Emittente"] = ""
    out["Valuta"] = df["Valuta"] if "Valuta" in df.columns else "EUR"

    # =========================
    # ✅ POSITION KEY
    # =========================
    out["PositionKey"] = np.where(
        out["ID"].notna(),
        out["ID"].astype(str).str.strip(),
        out["Ticker"].astype(str).str.strip()
    )

    # =========================
    # ✅ PULIZIA FINALE
    # =========================
    out = out.dropna(subset=["Ticker", "Data", "Quantita"])
    out = out[out["Ticker"] != ""]
    out = out.sort_values(["Data", "Ticker"]).reset_index(drop=True)

    return out
