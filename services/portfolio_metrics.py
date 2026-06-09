import numpy as np
import pandas as pd


def compute_portfolio_xirr(ops_enriched, dividends, final_value, valuation_date=None):
    ops = ops_enriched.copy()
    ops["Data"] = pd.to_datetime(ops["Data"])
    ops["CashflowCalc"] = pd.to_numeric(ops["CashflowCalc"], errors="coerce").fillna(0.0)

    # --- flussi operazioni
    ops_flows = ops.groupby("Data")["CashflowCalc"].sum().rename("Operazioni")

    # --- flussi dividendi
    if dividends is not None and not dividends.empty:
        div = dividends.copy()
        div["Data"] = pd.to_datetime(div["Data"])
        div["DividendoNetto"] = pd.to_numeric(div["DividendoNetto"], errors="coerce").fillna(0.0)
        div_flows = div.groupby("Data")["DividendoNetto"].sum().rename("Dividendi")
    else:
        div_flows = pd.Series(dtype=float, name="Dividendi")

    # --- data finale
    max_dates = []
    if not ops_flows.empty:
        max_dates.append(ops_flows.index.max())
    if not div_flows.empty:
        max_dates.append(div_flows.index.max())

    if valuation_date is None:
        if max_dates:
            valuation_date = max(max_dates)
        else:
            return None, pd.DataFrame()

    valuation_date = pd.Timestamp(valuation_date)

    # --- valore finale (posizioni aperte)
    final_flow = pd.Series([final_value], index=[valuation_date], name="Valore finale")

    # --- unione flussi
    df = pd.concat([ops_flows, div_flows, final_flow], axis=1).fillna(0.0)
    df["Totale"] = df.sum(axis=1)

    df = df.sort_index().reset_index().rename(columns={"index": "Data"})

    flows = df["Totale"].values
    dates = pd.to_datetime(df["Data"])

    # serve almeno 1 positivo e 1 negativo
    if not ((flows > 0).any() and (flows < 0).any()):
        return None, df

    base = dates.iloc[0]
    t = np.array([(d - base).days / 365.25 for d in dates])

    def xnpv(rate):
        return np.sum(flows / (1 + rate) ** t)

    # --- Newton-Raphson
    rate = 0.1
    for _ in range(50):
        try:
            f = xnpv(rate)
            df_rate = np.sum(-t * flows / (1 + rate) ** (t + 1))
            new_rate = rate - f / df_rate

            if abs(new_rate - rate) < 1e-8:
                return new_rate, df

            rate = new_rate
        except:
            break

    # --- fallback semplice (bisection)
    low, high = -0.9, 5.0
    for _ in range(100):
        mid = (low + high) / 2
        if xnpv(low) * xnpv(mid) <= 0:
            high = mid
        else:
            low = mid

        if abs(high - low) < 1e-6:
            return mid, df

    return None, df
