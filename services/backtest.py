import numpy as np
import pandas as pd

def backtest_portfolio(
    current: pd.DataFrame,
    closes: pd.DataFrame,
    rebalance_frequency: str = "yearly",
    ticker_col: str = "Ticker",
    value_col: str = "Valore",
    initial_value=None,
):
    """
    Backtest della composizione ATTUALE del portafoglio.

    Logica
    ------
    1. Prende da `current` le posizioni attualmente aperte.
    2. Aggrega eventuali righe appartenenti allo stesso ticker.
    3. Calcola i pesi target dai valori correnti.
    4. Cerca la prima data storica in cui tutti i ticker
       hanno contemporaneamente un prezzo valido.
    5. Simula il portafoglio mantenendo liberi i pesi
       tra un ribilanciamento e il successivo.
    6. Ribilancia periodicamente ai pesi target.
    7. Il calendario dei ribilanciamenti parte dalla
       data iniziale del backtest.

    Frequenze supportate
    --------------------
    monthly
    quarterly
    semiannual
    yearly
    none

    Parameters
    ----------
    current : pd.DataFrame
        Portafoglio corrente. Deve contenere almeno
        Ticker e Valore.

    closes : pd.DataFrame
        Prezzi storici. Indice = data,
        colonne = ticker.

    rebalance_frequency : str
        Frequenza di ribilanciamento.

    ticker_col : str
        Nome colonna ticker in current.

    value_col : str
        Nome colonna valore posizione in current.

    initial_value : float, optional
        Capitale nozionale iniziale.

        Se None viene utilizzato il valore totale
        corrente delle posizioni incluse nel backtest.

        Questo valore serve come scala monetaria della
        simulazione e NON rappresenta necessariamente
        il capitale realmente posseduto alla data
        storica iniziale.

    Returns
    -------
    result : pd.DataFrame
        Storico simulato del portafoglio.

    target_weights : pd.Series
        Pesi target.

    initial_value : float
        Capitale nozionale iniziale.

    initial_date : pd.Timestamp
        Prima data comune con prezzi validi.
    """

    # ========================================================
    # Validazione
    # ========================================================

    if current is None or current.empty:
        raise ValueError(
            "current è vuoto."
        )

    if closes is None or closes.empty:
        raise ValueError(
            "closes è vuoto."
        )

    if ticker_col not in current.columns:
        raise ValueError(
            f"Colonna '{ticker_col}' non trovata "
            "nel portafoglio corrente."
        )

    if value_col not in current.columns:
        raise ValueError(
            f"Colonna '{value_col}' non trovata "
            "nel portafoglio corrente."
        )

    # ========================================================
    # Frequenze
    # ========================================================

    frequency_map = {
        "monthly": pd.DateOffset(months=1),
        "quarterly": pd.DateOffset(months=3),
        "semiannual": pd.DateOffset(months=6),
        "yearly": pd.DateOffset(years=1),
    }

    valid_frequencies = {
        "monthly",
        "quarterly",
        "semiannual",
        "yearly",
        "none",
    }

    if rebalance_frequency not in valid_frequencies:
        raise ValueError(
            "rebalance_frequency deve essere uno tra: "
            "'monthly', 'quarterly', 'semiannual', "
            "'yearly', 'none'."
        )

    # ========================================================
    # Copie
    # ========================================================

    current = current.copy()
    closes = closes.copy()

    # ========================================================
    # Pulizia portafoglio corrente
    # ========================================================

    current[ticker_col] = (
        current[ticker_col]
        .astype(str)
        .str.strip()
    )

    current[value_col] = pd.to_numeric(
        current[value_col],
        errors="coerce",
    )

    current = current.dropna(
        subset=[
            ticker_col,
            value_col,
        ]
    )

    # ========================================================
    # Solo posizioni realmente aperte
    #
    # Valore > 0 evita posizioni chiuse / nulle.
    # ========================================================

    current = current[
        current[value_col] > 0
    ].copy()

    if current.empty:
        raise ValueError(
            "Nessuna posizione aperta trovata "
            "nel portafoglio corrente."
        )

    # ========================================================
    # Aggregazione per ticker
    #
    # Se lo stesso ticker compare più volte,
    # sommiamo il valore.
    # ========================================================

    current_values = (
        current
        .groupby(ticker_col)[value_col]
        .sum()
        .sort_index()
    )

    current_values = current_values[
        current_values > 0
    ]

    if current_values.empty:
        raise ValueError(
            "Nessun valore utilizzabile trovato "
            "nel portafoglio corrente."
        )

    # ========================================================
    # Ticker target
    # ========================================================

    tickers = current_values.index.tolist()

    # ========================================================
    # Verifica prezzi disponibili
    # ========================================================

    missing_tickers = [
        ticker
        for ticker in tickers
        if ticker not in closes.columns
    ]

    if missing_tickers:
        raise ValueError(
            "Prezzi storici mancanti per: "
            + ", ".join(missing_tickers)
        )

    # ========================================================
    # Pesi target ATTUALI
    # ========================================================

    total_current_value = float(
        current_values.sum()
    )

    if (
        not np.isfinite(total_current_value)
        or total_current_value <= 0
    ):
        raise ValueError(
            "Valore totale corrente non valido."
        )

    target_weights = (
        current_values
        / total_current_value
    )

    # Normalizzazione di sicurezza
    target_weights = (
        target_weights
        / target_weights.sum()
    )

    # ========================================================
    # Capitale nozionale iniziale
    #
    # Default:
    # valore corrente totale delle posizioni.
    # ========================================================

    if initial_value is None:

        initial_value = total_current_value

    else:

        initial_value = float(
            initial_value
        )

    if (
        not np.isfinite(initial_value)
        or initial_value <= 0
    ):
        raise ValueError(
            "initial_value deve essere maggiore di zero."
        )

    # ========================================================
    # Preparazione prezzi
    # ========================================================

    closes.index = pd.to_datetime(
        closes.index,
        errors="coerce",
    )

    closes = closes.loc[
        ~closes.index.isna()
    ]

    closes = closes.sort_index()

    prices = closes[
        tickers
    ].copy()

    prices = prices.apply(
        pd.to_numeric,
        errors="coerce",
    )

    prices = prices.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    # ========================================================
    # Forward fill
    #
    # Utile per festività differenti fra mercati.
    #
    # Non crea dati precedenti alla prima quotazione:
    # i NaN iniziali restano NaN.
    # ========================================================

    prices = prices.ffill()

    # ========================================================
    # Prima data comune
    #
    # Dopo ffill, dropna elimina tutte le date precedenti
    # alla disponibilità contemporanea di tutti i ticker.
    # ========================================================

    prices = prices.dropna(
        how="any"
    )

    # Prezzi devono essere positivi
    prices = prices[
        (prices > 0).all(axis=1)
    ]

    if len(prices) < 2:
        raise ValueError(
            "Non esiste uno storico comune sufficiente "
            "per tutti i ticker attuali."
        )

    initial_date = prices.index[0]

    # ========================================================
    # Rendimenti giornalieri
    # ========================================================

    asset_returns = (
        prices
        .pct_change()
        .fillna(0.0)
    )

    # ========================================================
    # Allocazione iniziale simulata
    # ========================================================

    position_values = (
        target_weights
        * initial_value
    ).astype(float)

    # ========================================================
    # Calendario ribilanciamenti
    # ========================================================

    if rebalance_frequency == "none":

        next_rebalance_date = None

    else:

        next_rebalance_date = (
            initial_date
            + frequency_map[
                rebalance_frequency
            ]
        )

    # ========================================================
    # Simulazione
    # ========================================================

    records = []

    for i, date in enumerate(prices.index):

        rebalanced = False

        scheduled_rebalance_date = pd.NaT

        # ====================================================
        # Dal secondo giorno:
        # applicazione rendimenti
        # ====================================================

        if i > 0:

            position_values = (
                position_values
                * (
                    1.0
                    + asset_returns.loc[date]
                )
            )

            # =================================================
            # Rebalance
            #
            # Se la data teorica non è presente nello storico,
            # viene utilizzata la prima data disponibile
            # successiva.
            # =================================================

            while (
                next_rebalance_date is not None
                and date >= next_rebalance_date
            ):

                scheduled_rebalance_date = (
                    next_rebalance_date
                )

                portfolio_value = float(
                    position_values.sum()
                )

                # ---------------------------------------------
                # Reset ai target
                # ---------------------------------------------

                position_values = (
                    target_weights
                    * portfolio_value
                )

                rebalanced = True

                # ---------------------------------------------
                # Prossima scadenza
                # ---------------------------------------------

                next_rebalance_date = (
                    next_rebalance_date
                    + frequency_map[
                        rebalance_frequency
                    ]
                )

        # ====================================================
        # Valore portafoglio
        # ====================================================

        portfolio_value = float(
            position_values.sum()
        )

        # ====================================================
        # Pesi effettivi
        # ====================================================

        if portfolio_value > 0:

            actual_weights = (
                position_values
                / portfolio_value
            )

        else:

            actual_weights = pd.Series(
                np.nan,
                index=position_values.index,
            )

        # ====================================================
        # Record
        # ====================================================

        row = {
            "Data": date,
            "Valore portafoglio": portfolio_value,
            "Ribilanciamento": rebalanced,
            "Data teorica ribilanciamento":
                scheduled_rebalance_date,
        }

        # ====================================================
        # Valore + peso di ogni ticker
        # ====================================================

        for ticker in target_weights.index:

            row[
                f"Valore {ticker}"
            ] = float(
                position_values[ticker]
            )

            row[
                f"Peso {ticker}"
            ] = float(
                actual_weights[ticker]
            )

        records.append(row)

    # ========================================================
    # DataFrame risultato
    # ========================================================

    result = (
        pd.DataFrame(records)
        .set_index("Data")
    )

    # ========================================================
    # Rendimenti
    # ========================================================

    result["Rendimento giornaliero"] = (
        result["Valore portafoglio"]
        .pct_change()
        .fillna(0.0)
    )

    result["Rendimento cumulato"] = (
        result["Valore portafoglio"]
        / initial_value
        - 1.0
    )

    # ========================================================
    # Metadata
    # ========================================================

    result.attrs["initial_date"] = (
        initial_date
    )

    result.attrs["initial_value"] = (
        initial_value
    )

    result.attrs["rebalance_frequency"] = (
        rebalance_frequency
    )

    result.attrs["target_weights"] = (
        target_weights.to_dict()
    )

    result.attrs["tickers"] = (
        list(target_weights.index)
    )

    # ========================================================
    # Return
    # ========================================================

    return (
        result,
        target_weights,
        initial_value,
        initial_date,
    )
    
def build_backtest_benchmark(
    benchmark_prices: pd.Series,
    backtest_index: pd.DatetimeIndex,
    initial_value: float,
    ):
    """
    Costruisce il benchmark dedicato al backtest.

    Simula l'investimento dello stesso capitale iniziale
    del backtest interamente nel benchmark.

    Il benchmark viene allineato alle stesse date
    del portafoglio simulato.
    """

    # ========================================================
    # Controlli iniziali
    # ========================================================

    if benchmark_prices is None:
        return None

    if backtest_index is None or len(backtest_index) == 0:
        return None

    if initial_value is None or initial_value <= 0:
        return None

    benchmark_prices = benchmark_prices.copy()

    # ========================================================
    # Preparazione indice
    # ========================================================

    benchmark_prices.index = pd.to_datetime(
        benchmark_prices.index,
        errors="coerce",
    )

    benchmark_prices = benchmark_prices.loc[
        ~benchmark_prices.index.isna()
    ]

    benchmark_prices = benchmark_prices.sort_index()

    # ========================================================
    # Preparazione prezzi
    # ========================================================

    benchmark_prices = pd.to_numeric(
        benchmark_prices,
        errors="coerce",
    )

    benchmark_prices = benchmark_prices.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    benchmark_prices = benchmark_prices.dropna()

    benchmark_prices = benchmark_prices[
        benchmark_prices > 0
    ]

    if benchmark_prices.empty:
        return None

    # ========================================================
    # Periodo backtest
    # ========================================================

    backtest_index = pd.DatetimeIndex(
        pd.to_datetime(
            backtest_index,
            errors="coerce",
        )
    )

    backtest_index = backtest_index[
        ~backtest_index.isna()
    ]

    backtest_index = backtest_index.sort_values()

    if len(backtest_index) == 0:
        return None

    backtest_start = backtest_index[0]
    backtest_end = backtest_index[-1]

    # Manteniamo anche le quotazioni antecedenti alla prima
    # data del backtest, perché possono servire per trovare
    # l'ultimo prezzo disponibile.
    benchmark_prices = benchmark_prices.loc[
        benchmark_prices.index <= backtest_end
    ]

    if benchmark_prices.empty:
        return None

    # ========================================================
    # Verifica disponibilità benchmark alla partenza
    # ========================================================

    available_at_start = benchmark_prices.loc[
        benchmark_prices.index <= backtest_start
    ]

    if available_at_start.empty:
        # Il benchmark non dispone ancora di un prezzo
        # alla data iniziale del backtest.
        return None

    # ========================================================
    # Allineamento alle date del backtest
    # ========================================================

    aligned_prices = benchmark_prices.reindex(
        backtest_index,
        method="ffill",
    )

    aligned_prices = pd.to_numeric(
        aligned_prices,
        errors="coerce",
    )

    if aligned_prices.empty:
        return None

    first_price = aligned_prices.iloc[0]

    if (
        pd.isna(first_price)
        or first_price <= 0
    ):
        return None

    # ========================================================
    # Investimento iniziale
    #
    # Tutto il capitale viene investito nel benchmark
    # alla prima data del backtest.
    # ========================================================

    benchmark_quantity = (
        float(initial_value)
        / float(first_price)
    )

    # ========================================================
    # Evoluzione buy & hold
    # ========================================================

    benchmark_value = (
        aligned_prices
        * benchmark_quantity
    )

    benchmark_value.name = "Valore benchmark"

    return benchmark_value
