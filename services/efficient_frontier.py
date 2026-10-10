from __future__ import annotations

import numpy as np
import pandas as pd


TRADING_DAYS = 252


def calculate_efficient_frontier(
    closes: pd.DataFrame,
    current_weights: pd.Series,
    num_portfolios: int = 50_000,
    use_risk_free: bool = False,
    risk_free_rate: float = 0.0,
    seed: int = 42,
):
    """
    Simulazione Monte Carlo rischio/rendimento.

    Parameters
    ----------
    closes:
        Prezzi storici degli asset.
        Devono essere già convertiti in EUR.

    current_weights:
        Series indicizzata per ticker contenente
        i pesi del portafoglio corrente.

    num_portfolios:
        Numero di portafogli casuali da simulare.

    use_risk_free:
        Se True, lo Sharpe viene calcolato sottraendo
        il risk free rate.

    risk_free_rate:
        Tasso risk free annualizzato espresso
        in forma decimale.
        Esempio: 0.02 = 2%.

    seed:
        Seed della simulazione Monte Carlo.

    Returns
    -------
    dict oppure None
    """

    # ========================================================
    # Controlli iniziali
    # ========================================================

    if closes is None or closes.empty:
        return None

    if current_weights is None or current_weights.empty:
        return None

    if num_portfolios <= 0:
        return None

    # ========================================================
    # Asset utilizzabili
    # ========================================================

    assets = [
        ticker
        for ticker in current_weights.index
        if (
            ticker in closes.columns
            and current_weights[ticker] > 0
        )
    ]

    if len(assets) < 2:
        return None

    # ========================================================
    # Prezzi
    # ========================================================

    prices = (
        closes[assets]
        .copy()
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
    )

    # Periodo comune a tutti gli asset
    prices = prices.dropna(
        how="any"
    )

    if prices.empty or len(prices) < 2:
        return None

    # ========================================================
    # Rendimenti giornalieri
    # ========================================================

    returns = (
        prices
        .pct_change(fill_method=None)
        .dropna(how="any")
    )

    if returns.empty:
        return None

    # ========================================================
    # Parametri annualizzati
    # ========================================================

    mean_returns = (
        returns.mean()
        * TRADING_DAYS
    )

    cov_matrix = (
        returns.cov()
        * TRADING_DAYS
    )

    # ========================================================
    # Monte Carlo
    # ========================================================

    num_assets = len(assets)

    rng = np.random.default_rng(
        seed
    )

    weights_matrix = rng.random(
        (
            num_portfolios,
            num_assets,
        )
    )

    weights_matrix /= (
        weights_matrix.sum(
            axis=1,
            keepdims=True,
        )
    )

    # ========================================================
    # Rendimento portafogli simulati
    # ========================================================

    portfolio_returns = (
        weights_matrix
        @ mean_returns.values
    )

    # ========================================================
    # Volatilità portafogli simulati
    # ========================================================

    portfolio_variances = np.einsum(
        "ij,jk,ik->i",
        weights_matrix,
        cov_matrix.values,
        weights_matrix,
    )

    portfolio_volatility = np.sqrt(
        portfolio_variances
    )

    # ========================================================
    # Sharpe Ratio
    # ========================================================

    if use_risk_free:
        excess_returns = (
            portfolio_returns
            - risk_free_rate
        )
    else:
        excess_returns = (
            portfolio_returns
        )

    sharpe_ratios = np.divide(
        excess_returns,
        portfolio_volatility,
        out=np.full(
            num_portfolios,
            np.nan,
        ),
        where=portfolio_volatility > 0,
    )

    # ========================================================
    # Portafogli speciali
    # ========================================================

    min_vol_idx = int(
        np.nanargmin(
            portfolio_volatility
        )
    )

    max_return_idx = int(
        np.nanargmax(
            portfolio_returns
        )
    )

    #=========================================================
    # ***** DEBUG 
    #=========================================================
    print(
        "RF:",
        risk_free_rate
    )
    
    print(
        "Return min/max:",
        np.nanmin(portfolio_returns),
        np.nanmax(portfolio_returns),
    )
    
    print(
        "Volatility min/max:",
        np.nanmin(portfolio_volatility),
        np.nanmax(portfolio_volatility),
    )
    
    print(
        "NaN sharpe:",
        np.isnan(sharpe_ratios).sum()
    )
    
    print(
        "Total sharpe:",
        len(sharpe_ratios)
    )
    #=========================================================
    max_sharpe_idx = int(
        np.nanargmax(
            sharpe_ratios
        )
    )

    # ========================================================
    # Portafoglio corrente
    # ========================================================

    my_weights = (
        current_weights
        .reindex(assets)
        .fillna(0.0)
        .astype(float)
    )

    my_weight_total = float(
        my_weights.sum()
    )

    if my_weight_total <= 0:
        return None

    my_weights = (
        my_weights
        / my_weight_total
    )

    my_weights_array = (
        my_weights.values
    )

    my_return = float(
        my_weights_array
        @ mean_returns.values
    )

    my_variance = float(
        my_weights_array.T
        @ cov_matrix.values
        @ my_weights_array
    )

    my_volatility = float(
        np.sqrt(my_variance)
    )

    if my_volatility > 0:

        if use_risk_free:
            my_excess_return = (
                my_return
                - risk_free_rate
            )
        else:
            my_excess_return = (
                my_return
            )

        my_sharpe = (
            my_excess_return
            / my_volatility
        )

    else:
        my_sharpe = np.nan

    # ========================================================
    # DataFrame simulazioni
    # ========================================================

    simulations = pd.DataFrame(
        {
            "Return":
                portfolio_returns,

            "Volatility":
                portfolio_volatility,

            "Sharpe":
                sharpe_ratios,
        }
    )

    # ========================================================
    # Helper portafoglio
    # ========================================================

    def build_portfolio_result(
        index: int,
    ) -> dict:

        weights = pd.Series(
            weights_matrix[index],
            index=assets,
            name="Weight",
        )

        return {
            "return":
                float(
                    portfolio_returns[index]
                ),

            "volatility":
                float(
                    portfolio_volatility[index]
                ),

            "sharpe":
                float(
                    sharpe_ratios[index]
                ),

            "weights":
                weights,
        }

    # ========================================================
    # Risultato
    # ========================================================

    return {
        "assets":
            assets,

        "start_date":
            prices.index.min(),

        "end_date":
            prices.index.max(),

        "mean_returns":
            mean_returns,

        "cov_matrix":
            cov_matrix,

        "simulations":
            simulations,
        
        "weights_matrix":
            weights_matrix,
        
        "min_volatility":
            build_portfolio_result(
                min_vol_idx
            ),

        "max_return":
            build_portfolio_result(
                max_return_idx
            ),

        "max_sharpe":
            build_portfolio_result(
                max_sharpe_idx
            ),

        "current_portfolio": {
            "return":
                my_return,

            "volatility":
                my_volatility,

            "sharpe":
                float(my_sharpe),

            "weights":
                my_weights,
        },

        "use_risk_free":
            use_risk_free,

        "risk_free_rate":
            (
                float(risk_free_rate)
                if use_risk_free
                else 0.0
            ),

        "num_portfolios":
            num_portfolios,
    }
