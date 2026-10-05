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

# def backtest_initial_portfolio(
#     holdings: pd.DataFrame,
#     ops_enriched: pd.DataFrame,
#     closes: pd.DataFrame,
#     rebalance_frequency: str = "yearly",
#     position_key_col: str = "PositionKey",
#     ticker_col: str = "Ticker",
# ):
#     """
#     Backtest ipotetico basato sulla composizione iniziale reale
#     del portafoglio.

#     La funzione:

#     1. Ricava la mappatura PositionKey -> Ticker.
#     2. Trova la prima data in cui tutte le posizioni sono attive.
#     3. Verifica che nella stessa data esistano prezzi validi.
#     4. Calcola il valore iniziale:
#            quantità * prezzo
#     5. Calcola i pesi target iniziali.
#     6. Simula l'andamento del portafoglio.
#     7. Ribilancia ai pesi iniziali con frequenza:
#            monthly
#            quarterly
#            semiannual
#            yearly
#            none
#     8. Il calendario di ribilanciamento è ancorato
#        alla data iniziale del backtest.

#     Returns
#     -------
#     result : pd.DataFrame
#         Serie storica del portafoglio simulato.

#     target_weights : pd.Series
#         Pesi target iniziali.

#     initial_value : float
#         Valore iniziale reale del portafoglio.

#     initial_date : pd.Timestamp
#         Prima data valida del backtest.
#     """

#     # ========================================================
#     # Validazione input
#     # ========================================================

#     if holdings is None or holdings.empty:
#         raise ValueError("holdings è vuoto.")

#     if ops_enriched is None or ops_enriched.empty:
#         raise ValueError("ops_enriched è vuoto.")

#     if closes is None or closes.empty:
#         raise ValueError("closes è vuoto.")

#     if position_key_col not in ops_enriched.columns:
#         raise ValueError(
#             f"Colonna '{position_key_col}' non trovata "
#             "in ops_enriched."
#         )

#     if ticker_col not in ops_enriched.columns:
#         raise ValueError(
#             f"Colonna '{ticker_col}' non trovata "
#             "in ops_enriched."
#         )

#     # ========================================================
#     # Frequenze supportate
#     # ========================================================

#     frequency_map = {
#         "monthly": pd.DateOffset(months=1),
#         "quarterly": pd.DateOffset(months=3),
#         "semiannual": pd.DateOffset(months=6),
#         "yearly": pd.DateOffset(years=1),
#     }

#     valid_frequencies = {
#         "monthly",
#         "quarterly",
#         "semiannual",
#         "yearly",
#         "none",
#     }

#     if rebalance_frequency not in valid_frequencies:
#         raise ValueError(
#             "rebalance_frequency deve essere uno tra: "
#             "'monthly', 'quarterly', 'semiannual', "
#             "'yearly', 'none'."
#         )

#     # ========================================================
#     # Copie dati
#     # ========================================================

#     holdings = holdings.copy()
#     closes = closes.copy()

#     # ========================================================
#     # Normalizzazione date
#     # ========================================================

#     holdings.index = pd.to_datetime(
#         holdings.index,
#         errors="coerce",
#     )

#     closes.index = pd.to_datetime(
#         closes.index,
#         errors="coerce",
#     )

#     holdings = (
#         holdings.loc[
#             ~holdings.index.isna()
#         ]
#         .sort_index()
#     )

#     closes = (
#         closes.loc[
#             ~closes.index.isna()
#         ]
#         .sort_index()
#     )

#     # ========================================================
#     # PositionKey -> Ticker
#     # ========================================================

#     mapping_df = (
#         ops_enriched[
#             [position_key_col, ticker_col]
#         ]
#         .dropna()
#         .drop_duplicates()
#     )

#     # Un PositionKey non deve appartenere
#     # contemporaneamente a ticker diversi
#     ticker_count = (
#         mapping_df
#         .groupby(position_key_col)[ticker_col]
#         .nunique()
#     )

#     invalid_keys = ticker_count[
#         ticker_count > 1
#     ]

#     if not invalid_keys.empty:
#         raise ValueError(
#             "Uno o più PositionKey risultano associati "
#             "a ticker differenti."
#         )

#     position_to_ticker = (
#         mapping_df
#         .set_index(position_key_col)[ticker_col]
#         .to_dict()
#     )

#     # ========================================================
#     # Holdings può avere colonne int o string
#     # ========================================================

#     holdings_column_map = {
#         str(column): column
#         for column in holdings.columns
#     }

#     # ========================================================
#     # Posizioni utilizzabili
#     # ========================================================

#     positions = []

#     for position_key, ticker in position_to_ticker.items():

#         key = str(position_key)

#         if key not in holdings_column_map:
#             continue

#         if ticker not in closes.columns:
#             raise ValueError(
#                 f"Prezzi mancanti per il ticker: {ticker}"
#             )

#         positions.append(
#             {
#                 "position_key": position_key,
#                 "holdings_column": holdings_column_map[key],
#                 "ticker": ticker,
#             }
#         )

#     if not positions:
#         raise ValueError(
#             "Nessuna posizione valida trovata."
#         )

#     positions = pd.DataFrame(positions)

#     # ========================================================
#     # Quantità storiche
#     # ========================================================

#     holding_columns = (
#         positions["holdings_column"]
#         .tolist()
#     )

#     quantities = (
#         holdings[holding_columns]
#         .apply(
#             pd.to_numeric,
#             errors="coerce",
#         )
#         .fillna(0.0)
#     )

#     # ========================================================
#     # Prima data in cui TUTTE le posizioni sono attive
#     #
#     # In questo backtest interpretiamo "attiva"
#     # come quantità > 0.
#     # ========================================================

#     all_active_mask = (
#         quantities > 0
#     ).all(axis=1)

#     active_dates = quantities.index[
#         all_active_mask
#     ]

#     if len(active_dates) == 0:
#         raise ValueError(
#             "Non esiste una data in cui tutte le "
#             "posizioni siano contemporaneamente attive."
#         )

#     # ========================================================
#     # Troviamo la prima data con:
#     #
#     # - tutte le posizioni attive
#     # - tutti i prezzi disponibili e > 0
#     # ========================================================

#     tickers = (
#         positions["ticker"]
#         .drop_duplicates()
#         .tolist()
#     )

#     candidate_dates = (
#         active_dates
#         .intersection(closes.index)
#         .sort_values()
#     )

#     initial_date = None

#     for date in candidate_dates:

#         prices_day = pd.to_numeric(
#             closes.loc[
#                 date,
#                 tickers,
#             ],
#             errors="coerce",
#         )

#         if (
#             prices_day.notna().all()
#             and np.isfinite(prices_day).all()
#             and (prices_day > 0).all()
#         ):
#             initial_date = date
#             break

#     if initial_date is None:
#         raise ValueError(
#             "Nessuna data iniziale con quantità "
#             "e prezzi validi per tutti i ticker."
#         )

#     # ========================================================
#     # Quantità iniziali aggregate per ticker
#     #
#     # Questo gestisce anche il caso in cui più PositionKey
#     # appartengano allo stesso ticker.
#     # ========================================================

#     initial_quantities = {}

#     for _, position in positions.iterrows():

#         ticker = position["ticker"]
#         column = position["holdings_column"]

#         quantity = pd.to_numeric(
#             holdings.at[
#                 initial_date,
#                 column,
#             ],
#             errors="coerce",
#         )

#         if pd.isna(quantity):
#             quantity = 0.0

#         initial_quantities[ticker] = (
#             initial_quantities.get(
#                 ticker,
#                 0.0,
#             )
#             + float(quantity)
#         )

#     initial_quantities = pd.Series(
#         initial_quantities,
#         dtype=float,
#     )
#     # ========================================================
#     # Prezzi iniziali
#     # ========================================================

#     initial_prices = pd.to_numeric(
#         closes.loc[
#             initial_date,
#             initial_quantities.index,
#         ],
#         errors="coerce",
#     )

#     # ========================================================
#     # Valore iniziale di ogni ticker
#     # ========================================================

#     initial_position_values = (
#         initial_quantities
#         * initial_prices
#     )

#     # ========================================================
#     # Valore iniziale totale del portafoglio
#     # ========================================================

#     initial_value = float(
#         initial_position_values.sum()
#     )

#     if (
#         not np.isfinite(initial_value)
#         or initial_value <= 0
#     ):
#         raise ValueError(
#             "Valore iniziale del portafoglio non valido."
#         )

#     # ========================================================
#     # Pesi target iniziali
#     # ========================================================

#     target_weights = (
#         initial_position_values
#         / initial_value
#     )

#     target_weights = (
#         target_weights
#         / target_weights.sum()
#     )

#     # ========================================================
#     # Prezzi utilizzati dal backtest
#     # ========================================================

#     prices = closes[
#         target_weights.index
#     ].copy()

#     prices = prices.loc[
#         prices.index >= initial_date
#     ]

#     prices = prices.apply(
#         pd.to_numeric,
#         errors="coerce",
#     )

#     prices = prices.replace(
#         [np.inf, -np.inf],
#         np.nan,
#     )

#     # Il backtest procede soltanto sulle date
#     # in cui tutti i ticker hanno un prezzo valido
#     prices = prices.dropna(
#         how="any"
#     )

#     if len(prices) < 2:
#         raise ValueError(
#             "Storico prezzi insufficiente "
#             "per eseguire il backtest."
#         )

#     # ========================================================
#     # Rendimenti giornalieri dei ticker
#     # ========================================================

#     asset_returns = (
#         prices
#         .pct_change()
#         .fillna(0.0)
#     )

#     # ========================================================
#     # Valore iniziale delle singole posizioni
#     # ========================================================

#     position_values = (
#         target_weights
#         * initial_value
#     ).astype(float)

#     # ========================================================
#     # Prima data teorica di ribilanciamento
#     # ========================================================

#     if rebalance_frequency == "none":
#         next_rebalance_date = None
#     else:
#         next_rebalance_date = (
#             initial_date
#             + frequency_map[
#                 rebalance_frequency
#             ]
#         )

#     # ========================================================
#     # Simulazione
#     # ========================================================

#     records = []

#     for i, date in enumerate(prices.index):

#         rebalanced = False
#         scheduled_rebalance_date = pd.NaT

#         # ====================================================
#         # Dal secondo giorno applichiamo i rendimenti
#         # ====================================================

#         if i > 0:

#             position_values = (
#                 position_values
#                 * (
#                     1.0
#                     + asset_returns.loc[date]
#                 )
#             )

#             # =================================================
#             # Ribilanciamento
#             #
#             # Il calendario parte da initial_date.
#             #
#             # Se la data teorica cade in un giorno senza
#             # quotazioni, il ribilanciamento avviene alla
#             # prima data disponibile successiva.
#             # =================================================

#             while (
#                 next_rebalance_date is not None
#                 and date >= next_rebalance_date
#             ):

#                 scheduled_rebalance_date = (
#                     next_rebalance_date
#                 )

#                 total_value = float(
#                     position_values.sum()
#                 )

#                 position_values = (
#                     target_weights
#                     * total_value
#                 )

#                 rebalanced = True

#                 next_rebalance_date = (
#                     next_rebalance_date
#                     + frequency_map[
#                         rebalance_frequency
#                     ]
#                 )

#         # ====================================================
#         # Valore totale portafoglio
#         # ====================================================

#         total_value = float(
#             position_values.sum()
#         )

#         # ====================================================
#         # Pesi effettivi della giornata
#         # ====================================================

#         if total_value > 0:

#             actual_weights = (
#                 position_values
#                 / total_value
#             )

#         else:

#             actual_weights = pd.Series(
#                 np.nan,
#                 index=position_values.index,
#             )

#         # ====================================================
#         # Record giornaliero
#         # ====================================================

#         row = {
#             "Data": date,
#             "Valore portafoglio": total_value,
#             "Ribilanciamento": rebalanced,
#             "Data teorica ribilanciamento":
#                 scheduled_rebalance_date,
#         }

#         for ticker in target_weights.index:

#             row[
#                 f"Valore {ticker}"
#             ] = float(
#                 position_values[ticker]
#             )

#             row[
#                 f"Peso {ticker}"
#             ] = float(
#                 actual_weights[ticker]
#             )

#         records.append(row)

#     # ========================================================
#     # DataFrame finale
#     # ========================================================

#     result = (
#         pd.DataFrame(records)
#         .set_index("Data")
#     )

#     # ========================================================
#     # Rendimento giornaliero portafoglio
#     # ========================================================

#     result["Rendimento giornaliero"] = (
#         result["Valore portafoglio"]
#         .pct_change()
#         .fillna(0.0)
#     )

#     # ========================================================
#     # Rendimento cumulato
#     # ========================================================

#     result["Rendimento cumulato"] = (
#         result["Valore portafoglio"]
#         / initial_value
#         - 1.0
#     )

#     # ========================================================
#     # Metadata
#     # ========================================================

#     result.attrs["initial_date"] = (
#         initial_date
#     )

#     result.attrs["initial_value"] = (
#         initial_value
#     )

#     result.attrs["rebalance_frequency"] = (
#         rebalance_frequency
#     )

#     # ========================================================
#     # Return
#     # ========================================================

#     return (
#         result,
#         target_weights,
#         initial_value,
#         initial_date,
#     )
