# monte_carlo.py

import numpy as np
import pandas as pd
import yfinance as yf


TRADING_DAYS = 252


# ============================================================
# 1. Pulizia rendimenti
# ============================================================

def clean_returns(returns: pd.Series) -> pd.Series:
    """
    Pulisce una serie di rendimenti giornalieri.
    """

    r = pd.Series(returns, dtype=float).copy()

    r = (
        r.replace([np.inf, -np.inf], np.nan)
        .dropna()
    )

    return r


# ============================================================
# 2. Rendimenti da serie prezzi
# ============================================================

def returns_from_prices(prices: pd.Series) -> pd.Series:
    """
    Calcola i rendimenti giornalieri da una serie di prezzi.
    """

    prices = pd.Series(prices, dtype=float).dropna()

    if len(prices) < 2:
        return pd.Series(dtype=float)

    returns = prices.pct_change(fill_method=None)

    return clean_returns(returns)


# ============================================================
# 3. Download storico ticker esterno
# ============================================================

def download_ticker_history(
    ticker: str,
    period: str = "max",
) -> pd.Series:
    """
    Scarica da Yahoo Finance lo storico giornaliero
    di un ticker e restituisce la serie Close.
    """

    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("Ticker non valido.")

    data = yf.Ticker(ticker).history(
        period=period,
        interval="1d",
        auto_adjust=True,
    )

    if data is None or data.empty:
        raise ValueError(
            f"Nessun dato storico disponibile per {ticker}."
        )

    if "Close" not in data.columns:
        raise ValueError(
            f"Colonna Close non disponibile per {ticker}."
        )

    prices = data["Close"].copy()

    prices.index = pd.to_datetime(prices.index)

    # Rimuove timezone per uniformità con il resto dell'app
    if prices.index.tz is not None:
        prices.index = prices.index.tz_localize(None)

    prices = prices.dropna().sort_index()

    if len(prices) < 2:
        raise ValueError(
            f"Storico insufficiente per {ticker}."
        )

    prices.name = ticker

    return prices


# ============================================================
# 4. Stima parametri Monte Carlo
# ============================================================

def estimate_mc_parameters(
    returns: pd.Series,
    trading_days: int = TRADING_DAYS,
) -> dict:
    """
    Stima rendimento annualizzato e volatilità annualizzata
    dai rendimenti storici.

    Il rendimento annualizzato viene calcolato geometricamente
    utilizzando la durata temporale effettiva dello storico.

    La volatilità continua a essere annualizzata su 252
    sedute di mercato.
    """

    r = clean_returns(returns)

    if len(r) < 2:
        raise ValueError(
            "Numero di osservazioni insufficiente "
            "per stimare i parametri Monte Carlo."
        )

    # ========================================================
    # Rendimento cumulato
    # ========================================================

    growth = (1.0 + r).prod()

    # ========================================================
    # Durata reale dello storico
    # ========================================================

    if isinstance(r.index, pd.DatetimeIndex):

        start_date = r.index.min()
        end_date = r.index.max()

        days = (end_date - start_date).days

        if days <= 0:
            raise ValueError(
                "Periodo storico insufficiente "
                "per annualizzare il rendimento."
            )

        years = days / 365.25

    else:

        # Fallback per eventuali serie senza indice temporale
        start_date = None
        end_date = None

        years = len(r) / trading_days

    # ========================================================
    # Rendimento annualizzato geometrico
    # ========================================================

    if growth > 0 and years > 0:

        annual_return = (
            growth ** (1.0 / years)
            - 1.0
        )

    else:

        annual_return = np.nan

    # ========================================================
    # Volatilità annualizzata
    # ========================================================

    annual_volatility = (
        r.std(ddof=1)
        * np.sqrt(trading_days)
    )

    # ========================================================
    # Output
    # ========================================================

    return {
        "mu": float(annual_return),
        "sigma": float(annual_volatility),
        "observations": int(len(r)),
        "start_date": start_date,
        "end_date": end_date,
        "years": float(years),
    }
# ============================================================
# 5. Motore Monte Carlo
# ============================================================

# ============================================================
# Motore Monte Carlo (old) non ottimizzato 
# ============================================================

# def run_monte_carlo(
#     initial_value: float,
#     mu: float,
#     sigma: float,
#     years: int = 10,
#     n_simulations: int = 10_000,
#     trading_days: int = TRADING_DAYS,
#     seed: int | None = None,
# ) -> dict:
#     """
#     Simulazione Monte Carlo vettorializzata tramite
#     moto browniano geometrico.

#     Restituisce i percentili temporali e le statistiche finali.
#     """

#     if initial_value <= 0:
#         raise ValueError(
#             "Il capitale iniziale deve essere maggiore di zero."
#         )

#     if years <= 0:
#         raise ValueError(
#             "L'orizzonte temporale deve essere maggiore di zero."
#         )

#     if n_simulations <= 0:
#         raise ValueError(
#             "Il numero di simulazioni deve essere maggiore di zero."
#         )

#     if sigma < 0:
#         raise ValueError(
#             "La volatilità non può essere negativa."
#         )

#     if not np.isfinite(mu):
#         raise ValueError("Rendimento atteso non valido.")

#     if not np.isfinite(sigma):
#         raise ValueError("Volatilità non valida.")

#     n_days = int(years * trading_days)

#     rng = np.random.default_rng(seed)

#     # Incrementi casuali giornalieri
#     z = rng.standard_normal(
#         size=(n_days, n_simulations)
#     )

#     dt = 1.0 / trading_days

#     drift = (mu - 0.5 * sigma ** 2) * dt
#     diffusion = sigma * np.sqrt(dt) * z

#     log_returns = drift + diffusion

#     cumulative_log_returns = np.cumsum(
#         log_returns,
#         axis=0,
#     )

#     paths = initial_value * np.exp(
#         cumulative_log_returns
#     )

#     # Aggiunge il valore iniziale al giorno zero
#     initial_row = np.full(
#         (1, n_simulations),
#         initial_value,
#         dtype=float,
#     )

#     paths = np.vstack([
#         initial_row,
#         paths,
#     ])

#     # ========================================================
#     # Percentili lungo tutto l'orizzonte
#     # ========================================================

#     percentile_levels = [10, 25, 50, 75, 90]

#     percentiles = np.percentile(
#         paths,
#         percentile_levels,
#         axis=1,
#     )

#     timeline_years = (
#         np.arange(n_days + 1) / trading_days
#     )

#     percentile_paths = pd.DataFrame(
#         percentiles.T,
#         index=timeline_years,
#         columns=[
#             "P10",
#             "P25",
#             "P50",
#             "P75",
#             "P90",
#         ],
#     )

#     percentile_paths.index.name = "Years"

#     # ========================================================
#     # Valori finali
#     # ========================================================

#     final_values = paths[-1]

#     final_percentiles = {
#         "P10": float(np.percentile(final_values, 10)),
#         "P25": float(np.percentile(final_values, 25)),
#         "P50": float(np.percentile(final_values, 50)),
#         "P75": float(np.percentile(final_values, 75)),
#         "P90": float(np.percentile(final_values, 90)),
#     }

#     probability_loss = float(
#         np.mean(final_values < initial_value)
#     )

#     probability_gain = float(
#         np.mean(final_values > initial_value)
#     )

#     median_final_value = final_percentiles["P50"]

#     median_cagr = (
#         (median_final_value / initial_value)
#         ** (1.0 / years)
#         - 1.0
#     )

#     mean_final_value = float(
#         np.mean(final_values)
#     )

#     return {
#         "percentile_paths": percentile_paths,
#         "final_values": final_values,
#         "final_percentiles": final_percentiles,
#         "initial_value": float(initial_value),
#         "mean_final_value": mean_final_value,
#         "median_final_value": median_final_value,
#         "probability_loss": probability_loss,
#         "probability_gain": probability_gain,
#         "median_cagr": float(median_cagr),
#         "mu": float(mu),
#         "sigma": float(sigma),
#         "years": int(years),
#         "n_simulations": int(n_simulations),
#     }

# ============================================================
# Motore Monte Carlo  ottimizzato fa simulazioni ridotte e tiene i valori mensili
# ============================================================

def run_monte_carlo(
    initial_value: float,
    mu: float,
    sigma: float,
    years: int = 10,
    n_simulations: int = 10_000,
    trading_days: int = TRADING_DAYS,
    seed: int | None = None,
    batch_size: int = 2_000,
    points_per_year: int = 12,
) -> dict:
    """
    Simulazione Monte Carlo memory-efficient tramite
    moto browniano geometrico.

    Le simulazioni vengono elaborate a blocchi per ridurre
    drasticamente l'utilizzo di memoria.

    Per il fan chart vengono conservati solo alcuni punti
    temporali, per default uno al mese.

    L'interfaccia di output rimane compatibile con
    monte_carlo_view.py.
    """

    # ========================================================
    # Validazione
    # ========================================================

    if initial_value <= 0:
        raise ValueError(
            "Il capitale iniziale deve essere maggiore di zero."
        )

    if years <= 0:
        raise ValueError(
            "L'orizzonte temporale deve essere maggiore di zero."
        )

    if n_simulations <= 0:
        raise ValueError(
            "Il numero di simulazioni deve essere maggiore di zero."
        )

    if sigma < 0:
        raise ValueError(
            "La volatilità non può essere negativa."
        )

    if not np.isfinite(mu):
        raise ValueError(
            "Rendimento atteso non valido."
        )

    if not np.isfinite(sigma):
        raise ValueError(
            "Volatilità non valida."
        )

    # ========================================================
    # Parametri temporali
    # ========================================================

    n_days = int(years * trading_days)

    dt = 1.0 / trading_days

    drift = (
        mu - 0.5 * sigma ** 2
    ) * dt

    daily_sigma = (
        sigma * np.sqrt(dt)
    )

    # Circa un punto al mese
    n_points = int(
        years * points_per_year
    )

    sample_days = np.linspace(
        0,
        n_days,
        n_points + 1,
        dtype=int,
    )

    # Evita eventuali duplicati
    sample_days = np.unique(sample_days)

    timeline_years = (
        sample_days / trading_days
    )

    # ========================================================
    # Memoria risultati
    # ========================================================

    #
    # Questa matrice è molto più piccola:
    #
    # 10 anni:
    # circa 121 x 50.000
    #
    # invece di:
    # 2521 x 50.000
    #

    sampled_values = np.empty(
        (
            len(sample_days),
            n_simulations,
        ),
        dtype=np.float32,
    )

    final_values = np.empty(
        n_simulations,
        dtype=np.float64,
    )

    # Capitale iniziale
    sampled_values[0, :] = initial_value

    # ========================================================
    # Random generator
    # ========================================================

    rng = np.random.default_rng(seed)

    # ========================================================
    # Simulazione a blocchi
    # ========================================================

    for start in range(
        0,
        n_simulations,
        batch_size,
    ):

        end = min(
            start + batch_size,
            n_simulations,
        )

        current_batch_size = (
            end - start
        )

        # ----------------------------------------------------
        # Generiamo solo un batch
        # ----------------------------------------------------

        z = rng.standard_normal(
            size=(
                n_days,
                current_batch_size,
            )
        )

        # Log-rendimenti giornalieri
        log_returns = (
            drift
            + daily_sigma * z
        )

        # Rendimenti cumulati
        cumulative_log_returns = (
            np.cumsum(
                log_returns,
                axis=0,
            )
        )

        # ----------------------------------------------------
        # Campionamento mensile
        # ----------------------------------------------------

        for i in range(
            1,
            len(sample_days),
        ):

            day = sample_days[i]

            sampled_values[
                i,
                start:end
            ] = (
                initial_value
                * np.exp(
                    cumulative_log_returns[
                        day - 1
                    ]
                )
            )

        # ----------------------------------------------------
        # Valore finale
        # ----------------------------------------------------

        final_values[start:end] = (
            initial_value
            * np.exp(
                cumulative_log_returns[-1]
            )
        )

        # Il batch precedente può essere liberato
        del z
        del log_returns
        del cumulative_log_returns

    # ========================================================
    # Percentili fan chart
    # ========================================================

    percentile_levels = [
        10,
        25,
        50,
        75,
        90,
    ]

    percentiles = np.percentile(
        sampled_values,
        percentile_levels,
        axis=1,
    )

    percentile_paths = pd.DataFrame(
        percentiles.T,
        index=timeline_years,
        columns=[
            "P10",
            "P25",
            "P50",
            "P75",
            "P90",
        ],
    )

    percentile_paths.index.name = "Years"

    # ========================================================
    # Percentili finali
    # ========================================================

    final_percentiles = {
        "P10": float(
            np.percentile(
                final_values,
                10,
            )
        ),
        "P25": float(
            np.percentile(
                final_values,
                25,
            )
        ),
        "P50": float(
            np.percentile(
                final_values,
                50,
            )
        ),
        "P75": float(
            np.percentile(
                final_values,
                75,
            )
        ),
        "P90": float(
            np.percentile(
                final_values,
                90,
            )
        ),
    }

    # ========================================================
    # Probabilità
    # ========================================================

    probability_loss = float(
        np.mean(
            final_values < initial_value
        )
    )

    probability_gain = float(
        np.mean(
            final_values > initial_value
        )
    )

    # ========================================================
    # Mediana
    # ========================================================

    median_final_value = (
        final_percentiles["P50"]
    )

    median_cagr = (
        (
            median_final_value
            / initial_value
        )
        ** (1.0 / years)
        - 1.0
    )

    mean_final_value = float(
        np.mean(final_values)
    )

    # ========================================================
    # Output
    # ========================================================

    return {
        "percentile_paths": percentile_paths,
        "final_values": final_values,
        "final_percentiles": final_percentiles,

        "initial_value": float(
            initial_value
        ),

        "mean_final_value": (
            mean_final_value
        ),

        "median_final_value": (
            median_final_value
        ),

        "probability_loss": (
            probability_loss
        ),

        "probability_gain": (
            probability_gain
        ),

        "median_cagr": float(
            median_cagr
        ),

        "mu": float(mu),
        "sigma": float(sigma),

        "years": int(years),

        "n_simulations": int(
            n_simulations
        ),
    }

# ============================================================
# 6. Preparazione intero portafoglio
# ============================================================

def prepare_portfolio_mc(
    series: pd.DataFrame,
) -> tuple[float, pd.Series]:
    """
    Prepara capitale iniziale e rendimenti storici
    dell'intero portafoglio.
    """

    required_columns = {
        "Valore portafoglio",
        "P/L Totale Giornaliero %",
    }

    missing = required_columns.difference(
        series.columns
    )

    if missing:
        raise ValueError(
            f"Colonne mancanti in series: {sorted(missing)}"
        )

    values = (
        series["Valore portafoglio"]
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )

    if values.empty:
        raise ValueError(
            "Valore del portafoglio non disponibile."
        )

    initial_value = float(values.iloc[-1])

    returns = clean_returns(
        series["P/L Totale Giornaliero %"]
    )

    if returns.empty:
        raise ValueError(
            "Rendimenti storici del portafoglio non disponibili."
        )

    return initial_value, returns


# ============================================================
# 7. Preparazione ticker presente nel portafoglio
# ============================================================

def prepare_portfolio_ticker_mc(
    current: pd.DataFrame,
    closes: pd.DataFrame,
    ticker: str,
) -> tuple[float, pd.Series]:
    """
    Prepara capitale corrente e rendimenti storici
    di un ticker presente nel portafoglio.
    """

    ticker = ticker.strip()

    if "Ticker" not in current.columns:
        raise ValueError(
            "Colonna Ticker non disponibile in current."
        )

    if "Valore" not in current.columns:
        raise ValueError(
            "Colonna Valore non disponibile in current."
        )

    rows = current[
        current["Ticker"] == ticker
    ]

    if rows.empty:
        raise ValueError(
            f"{ticker} non presente nel portafoglio."
        )

    initial_value = float(
        rows["Valore"].sum()
    )

    if ticker not in closes.columns:
        raise ValueError(
            f"Storico prezzi non disponibile per {ticker}."
        )

    prices = closes[ticker].dropna()

    returns = returns_from_prices(prices)

    if returns.empty:
        raise ValueError(
            f"Storico insufficiente per {ticker}."
        )

    return initial_value, returns


# ============================================================
# 8. Preparazione ticker esterno
# ============================================================

def prepare_external_ticker_mc(
    ticker: str,
    initial_value: float,
    period: str = "max",
) -> tuple[float, pd.Series, pd.Series]:
    """
    Scarica lo storico di un ticker esterno e prepara
    gli input per il Monte Carlo.

    Restituisce:
        initial_value
        returns
        prices
    """

    if initial_value <= 0:
        raise ValueError(
            "Il capitale da simulare deve essere maggiore di zero."
        )

    prices = download_ticker_history(
        ticker=ticker,
        period=period,
    )

    returns = returns_from_prices(prices)

    if returns.empty:
        raise ValueError(
            f"Impossibile calcolare i rendimenti di {ticker}."
        )

    return (
        float(initial_value),
        returns,
        prices,
    )
