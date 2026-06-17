import pandas as pd
import numpy as np


def build_flow_adjusted_benchmark(flows_df: pd.DataFrame, benchmark_prices: pd.Series):
    """
    Costruisce un benchmark 'money weighted' usando i tuoi flussi nel tempo.

    flows_df:
        DataFrame con colonne:
        - Data
        - Operazioni
        - Dividendi   (opzionale)
    benchmark_prices:
        Serie pandas con index datetime e prezzo benchmark

    Ritorna:
        Serie valore benchmark nel tempo
    """

    if flows_df.empty or benchmark_prices.empty:
        return pd.Series(dtype=float)

    # copia difensiva
    df = flows_df.copy()

    # date normalizzate
    df["Data"] = pd.to_datetime(df["Data"]).dt.normalize()

    # prezzo benchmark ordinato
    prices = benchmark_prices.copy().sort_index()
    prices.index = pd.to_datetime(prices.index).normalize()
    prices = prices.groupby(level=0).last().sort_index().ffill()

    # flusso da replicare nel benchmark
    # Se usi Adj Close, puoi anche togliere Dividendi da qui
    flow_cols = [c for c in ["Operazioni", "Dividendi"] if c in df.columns]
    df["Flow"] = df[flow_cols].fillna(0.0).sum(axis=1)

    # aggrega per data
    daily_flows = df.groupby("Data")["Flow"].sum().sort_index()

    # trova il prezzo benchmark disponibile nelle date di flusso
    flow_prices = prices.reindex(daily_flows.index, method="ffill")

    # elimina date senza prezzo disponibile
    valid = flow_prices.notna()
    daily_flows = daily_flows[valid]
    flow_prices = flow_prices[valid]

    if daily_flows.empty:
        return pd.Series(dtype=float)

    # quote benchmark comprate/vendute dai flussi
    # negativo = investi -> compri quote
    # positivo = prelievo/disinvestimento -> vendi quote
    units_delta = -daily_flows / flow_prices

    # quote cumulative
    units = units_delta.cumsum()

    # riallinea le quote su tutte le date del benchmark
    units_daily = units.reindex(prices.index, method="ffill").fillna(0.0)

    # valore benchmark nel tempo
    benchmark_value = units_daily * prices
    benchmark_value.name = "Benchmark Flow Adjusted"

    return benchmark_value
