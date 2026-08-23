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



# def style_pl_column(col):
#     name = str(col.name).lower()

#     # intercetta tutte le colonne P/L (qualsiasi lingua)
#     if "p/l" in name:
#         return [
#             "color: #16A34A" if pd.notna(v) and v >= 0
#             else "color: #DC2626" if pd.notna(v)
#             else ""
#             for v in col
#         ]
#     return [""] * len(col)

def style_pl_column(col):
    name = str(col.name).lower()

    if "p/l" not in name:
        return [""] * len(col)

    is_7d = name in ["p/l 7 giorni", "p/l 7 giorni %"]

    styles = []

    for v in col:
        style = ""

        if is_7d:
            style += "background-color: #4B4C4D;"

        try:
            if pd.notna(v):
                val = float(v)

                if val >= 0:
                    style += "color:#16A34A;font-weight:bold;"
                else:
                    style += "color:#DC2626;font-weight:bold;"
        except (TypeError, ValueError):
            pass

        styles.append(style)

    return styles
