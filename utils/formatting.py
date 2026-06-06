from __future__ import annotations

import pandas as pd


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


def color_pl(val):
    if pd.isna(val):
        return ""
    if val > 0:
        return "color: #00ff00; font-weight: bold"
    if val < 0:
        return "color: #ff4d4d; font-weight: bold"
    return ""


def style_pl_column(col):
    if col.name in ["P/L", "P/L %", "P/L Netto Stimato", "P/L Giornaliero", "P/L Giornaliero %"]:
        return [color_pl(v) for v in col]
    return [""] * len(col)
