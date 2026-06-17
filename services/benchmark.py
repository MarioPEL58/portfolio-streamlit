import pandas as pd
import numpy as np

def build_flow_adjusted_benchmark(flows_df: pd.DataFrame, benchmark_prices: pd.Series):

    if flows_df.empty or benchmark_prices.empty:
        return pd.Series(dtype=float)

    df = flows_df.copy()

    # ✅ normalizza date
    df["Data"] = pd.to_datetime(df["Data"]).dt.normalize()

    # ✅ prezzi benchmark puliti
    prices = benchmark_prices.copy()
    prices.index = pd.to_datetime(prices.index).normalize()
    prices = prices.groupby(level=0).last().sort_index().ffill()

    # ✅ flussi già calcolati (Data + Flow)
    df["Flow"] = df["Flow"].fillna(0.0)

    # ✅ aggrega per data
    daily_flows = df.groupby("Data")["Flow"].sum().sort_index()

    # =========================
    # ✅ FIX CRITICO
    # =========================

    # allinea i prezzi ai flussi PRIMA di filtrare
    prices = prices.reindex(
        prices.index.union(daily_flows.index)
    ).sort_index().ffill()

    # ora i flussi hanno SEMPRE prezzo
    flow_prices = prices.reindex(daily_flows.index)

    # sicurezza
    valid = flow_prices.notna()
    daily_flows = daily_flows[valid]
    flow_prices = flow_prices[valid]

    if daily_flows.empty:
        return pd.Series(dtype=float)

    # ✅ quote benchmark
    units_delta = -daily_flows / flow_prices

    # ✅ cumulato
    units = units_delta.cumsum()

    # ✅ valore giornaliero
    units_daily = units.reindex(prices.index, method="ffill").fillna(0.0)

    benchmark_value = units_daily * prices
    benchmark_value.name = "Benchmark Flow Adjusted"

    return benchmark_value
