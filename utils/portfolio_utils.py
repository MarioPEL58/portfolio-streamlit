from __future__ import annotations

def build_ticker_names(ops):
    return (
        ops
        .dropna(subset=["Ticker"])
        .groupby("Ticker")["Nome"]
        .last()
        .fillna("")
        .to_dict()
    )
