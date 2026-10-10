import pandas as pd
import yfinance as yf
import numpy as np

def get_euro_risk_free_rate():
    """
    Stima il tasso risk-free EUR tramite ETF €STR (XEON).
    Ritorna valore ANNUALIZZATO (decimale, es. 0.021 = 2.1%)
    """
    
    ticker = "XEON.DE"

    data = yf.Ticker(ticker)
    df = data.history(period="1mo")
    
    close = (
        df["Close"]
        .dropna()
    )
    
    if len(close) < 2:
        return None
    
    prezzo_inizio = close.iloc[0]
    prezzo_fine = close.iloc[-1]
    
    giorni = (close.index[-1] - close.index[0]).days
    
    if giorni <= 0:
        return None
    
    rendimento_periodo = (prezzo_fine / prezzo_inizio) - 1
    
    # ✅ annualizzazione corretta
    rf_annual = ((1 + rendimento_periodo)** (365 / giorni) - 1)
    
    return float(rf_annual)
