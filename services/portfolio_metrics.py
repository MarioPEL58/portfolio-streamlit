import numpy as np
import pandas as pd
from scipy.stats import norm

def compute_portfolio_xirr(ops_enriched, dividends, final_value, valuation_date=None):
    ops = ops_enriched.copy()
    ops["Data"] = pd.to_datetime(ops["Data"], errors="coerce")
    ops["CashflowCalc"] = pd.to_numeric(ops["CashflowCalc"], errors="coerce").fillna(0.0)
    
    if "DateOnly" not in ops.columns:
        ops["DateOnly"] = ops["Data"].dt.normalize()

    # --- flussi operazioni
    ops_flows = ops.groupby("DateOnly")["CashflowCalc"].sum().rename("Operazioni")

    # --- flussi dividendi
    if dividends is not None and not dividends.empty:
        div = dividends.copy()
        div["Data"] = pd.to_datetime(div["Data"], errors="coerce")
        if "DateOnly" not in div.columns:
            div["DateOnly"] = div["Data"].dt.normalize()
        div["DividendoNetto"] = pd.to_numeric(div["DividendoNetto"], errors="coerce").fillna(0.0)
        div_flows = div.groupby("DateOnly")["DividendoNetto"].sum().rename("Dividendi")
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

def compute_var_historical(returns: pd.Series, confidence_level: float = 0.95):
    """
    Calcola il Value at Risk (VaR) Storico su base periodale (giornaliera).
    
    returns: 
        Serie dei rendimenti (consigliato: output di compute_flow_adjusted_returns).
    confidence_level: 
        Livello di confidenza (es. 0.95 per il 95%).
        
    Ritorna:
        Il VaR come valore positivo (es. 0.023 significa perdita massima del 2.3%).
    """
    if returns is None or returns.empty:
        return None
        
    # Isola il percentile associato al livello di rischio (1 - confidenza)
    percentile = (1.0 - confidence_level) * 100
    
    #np.percentile estrae il valore esatto. Usiamo il meno (-) per esprimerlo come perdita positiva
    var_value = -np.percentile(returns, percentile)
    
    return var_value


def compute_var_parametric(returns: pd.Series, confidence_level: float = 0.95):
    """
    Calcola il Value at Risk (VaR) Parametrico (Varianza-Covarianza).
    Assume una distribuzione normale dei rendimenti.
    
    returns: 
        Serie dei rendimenti.
    confidence_level: 
        Livello di confidenza (es. 0.95).
    """
    if returns is None or returns.empty:
        return None
        
    mean_return = returns.mean()
    std_return = returns.std()
    
    if std_return == 0 or np.isnan(std_return):
        return None
        
    # Calcola il valore Z critico (es. 1.645 per 95%)
    z_score = norm.ppf(confidence_level)
    
    # Formula standard: Z * std - mean (restituisce il valore già come perdita)
    var_value = (z_score * std_return) - mean_return
    
    return var_value


def compute_conditional_var(returns: pd.Series, confidence_level: float = 0.95):
    """
    Calcola il Conditional VaR (CVaR / Expected Shortfall).
    Rappresenta la perdita media attesa nei casi peggiori che superano il VaR storico.
    """
    if returns is None or returns.empty:
        return None
        
    # Per prima cosa serve il VaR Storico come soglia di rendimento negativo
    # (Attenzione: invertiamo il segno per confrontarlo direttamente con i rendimenti reali)
    var_threshold = -compute_var_historical(returns, confidence_level)
    
    # Isola solo i rendimenti che sono andati peggio della soglia VaR
    beyond_var_returns = returns[returns <= var_threshold]
    
    if beyond_var_returns.empty:
        return None
        
    # Il CVaR è la media di queste perdite estreme
    cvar_value = -beyond_var_returns.mean()
    
    return cvar_value
