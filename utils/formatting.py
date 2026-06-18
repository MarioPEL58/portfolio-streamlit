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
    name = str(col.name).lower()

    # intercetta tutte le colonne P/L (qualsiasi lingua)
    if "p/l" in name:
        return [
            "color: #16A34A" if pd.notna(v) and v >= 0
            else "color: #DC2626" if pd.notna(v)
            else ""
            for v in col
        ]
    return [""] * len(col)
