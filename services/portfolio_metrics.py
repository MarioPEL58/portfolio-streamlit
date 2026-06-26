import numpy as np
import pandas as pd


def compute_portfolio_xirr(ops_enriched, dividends, final_value, valuation_date=None):
    ops = ops_enriched.copy()
    ops["Data"] = pd.to_datetime(ops["Data"])
    ops["CashflowCalc"] = pd.to_numeric(ops["CashflowCalc"], errors="coerce").fillna(0.0)
    
    if "DateOnly" not in ops.columns:
        ops["DateOnly"] = ops["Data"].dt.normalize()

    # --- flussi operazioni
    ops_flows = ops.groupby("DataOnly")["CashflowCalc"].sum().rename("Operazioni")

    # --- flussi dividendi
    if dividends is not None and not dividends.empty:
        div = dividends.copy()
        div["Data"] = pd.to_datetime(div["Data"])
        if "DateOnly" not in div.columns:
            div["DateOnly"] = div["Data"].dt.normalize()
        div["DividendoNetto"] = pd.to_numeric(div["DividendoNetto"], errors="coerce").fillna(0.0)
        div_flows = div.groupby("DataOnly")["DividendoNetto"].sum().rename("Dividendi")
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

def compute_sharpe_ratio(
    portfolio_series: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
):
    """
    Calcola Sharpe ratio annualizzato.

    portfolio_series:
        Serie del valore portafoglio nel tempo (es: series["Valore portafoglio"])
    risk_free_rate:
        tasso risk-free giornaliero (default 0)
    periods_per_year:
        252 per dati giornalieri

    Ritorna:
        Sharpe ratio annualizzato
    """

    if portfolio_series is None or len(portfolio_series) < 2:
        return None

    # ✅ rendimenti giornalieri
    returns = portfolio_series.pct_change().dropna()

    if returns.empty:
        return None

    # ✅ media e volatilità
    mean_return = returns.mean()
    std_return = returns.std()

    if std_return == 0 or np.isnan(std_return):
        return None

    # ✅ Sharpe giornaliero
    sharpe_daily = (mean_return - risk_free_rate) / std_return

    # ✅ annualizzazione
    sharpe_annualized = sharpe_daily * np.sqrt(periods_per_year)

    return sharpe_annualized

def compute_flow_adjusted_returns(
    portfolio_value: pd.Series,
    flows_df: pd.DataFrame,
    flow_col: str = "Operazioni"
):
    """
    Calcola rendimenti giornalieri netti dai flussi esterni.

    portfolio_value:
        Serie del valore portafoglio nel tempo (index=datetime)

    flows_df:
        DataFrame con almeno:
        - Data
        - flow_col (es. Operazioni)

    flow_col:
        colonna dei flussi esterni da neutralizzare

    Ritorna:
        Serie dei rendimenti giornalieri netti dai flussi
    """

    if portfolio_value is None or portfolio_value.empty:
        return pd.Series(dtype=float)

    pv = portfolio_value.copy().sort_index()
    pv.index = pd.to_datetime(pv.index).normalize()

    flows = flows_df.copy()
    flows["Data"] = pd.to_datetime(flows["Data"]).dt.normalize()

    # aggrega flussi per data
    daily_flows = flows.groupby("Data")[flow_col].sum().sort_index()

    # riallinea i flussi alle date del portafoglio
    daily_flows = daily_flows.reindex(pv.index).fillna(0.0)

    prev_value = pv.shift(1)

    # rendimento netto dai flussi
    returns = (pv - prev_value + daily_flows) / prev_value
    returns = returns.replace([np.inf, -np.inf], np.nan).dropna()

    return returns
    
def compute_sharpe_from_returns(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
):
    if returns is None or returns.empty:
        return None

    mean_return = returns.mean()
    std_return = returns.std()

    if std_return == 0 or np.isnan(std_return):
        return None

    sharpe_daily = (mean_return - risk_free_rate) / std_return
    return sharpe_daily * np.sqrt(periods_per_year)

def compute_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
):
    """
    Calcola Sortino ratio annualizzato.

    returns:
        Serie rendimenti (meglio se già flow-adjusted ✅)
    """

    if returns is None or returns.empty:
        return None

    # ✅ rendimento medio
    mean_return = returns.mean()

    # ✅ seleziona solo rendimenti negativi rispetto al target
    downside_returns = returns[returns < risk_free_rate]

    if downside_returns.empty:
        return None

    # ✅ downside deviation
    downside_std = np.sqrt((downside_returns ** 2).mean())

    if downside_std == 0 or np.isnan(downside_std):
        return None

    # ✅ Sortino giornaliero
    sortino_daily = (mean_return - risk_free_rate) / downside_std

    # ✅ annualizzazione
    sortino_annual = sortino_daily * np.sqrt(periods_per_year)

    return sortino_annual

def compute_beta(portfolio_returns, benchmark_returns):
    """
    Calcola il Beta del portafoglio rispetto al benchmark
    """

    if portfolio_returns is None or benchmark_returns is None:
        return None

    # allinea serie
    df = portfolio_returns.to_frame("p").join(
        benchmark_returns.to_frame("b"),
        how="inner"
    ).dropna()

    if df.empty:
        return None

    cov = np.cov(df["p"], df["b"])[0][1]
    var = np.var(df["b"])

    if var == 0:
        return None

    beta = cov / var

    return beta
