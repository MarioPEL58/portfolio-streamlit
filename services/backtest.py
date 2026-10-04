import numpy as np
import pandas as pd


def backtest_initial_portfolio(
    holdings: pd.DataFrame,
    ops_enriched: pd.DataFrame,
    closes: pd.DataFrame,
    rebalance_frequency: str = "yearly",
    position_key_col: str = "PositionKey",
    ticker_col: str = "Ticker",
):
    """
    Backtest ipotetico basato sulla composizione iniziale reale
    del portafoglio.

    La funzione:

    1. Ricava la mappatura PositionKey -> Ticker.
    2. Trova la prima data in cui tutte le posizioni sono attive.
    3. Verifica che nella stessa data esistano prezzi validi.
    4. Calcola il valore iniziale:
           quantità * prezzo
    5. Calcola i pesi target iniziali.
    6. Simula l'andamento del portafoglio.
    7. Ribilancia ai pesi iniziali con frequenza:
           monthly
           quarterly
           semiannual
           yearly
           none
    8. Il calendario di ribilanciamento è ancorato
       alla data iniziale del backtest.

    Returns
    -------
    result : pd.DataFrame
        Serie storica del portafoglio simulato.

    target_weights : pd.Series
        Pesi target iniziali.

    initial_value : float
        Valore iniziale reale del portafoglio.

    initial_date : pd.Timestamp
        Prima data valida del backtest.
    """

    # ========================================================
    # Validazione input
    # ========================================================

    if holdings is None or holdings.empty:
        raise ValueError("holdings è vuoto.")

    if ops_enriched is None or ops_enriched.empty:
        raise ValueError("ops_enriched è vuoto.")

    if closes is None or closes.empty:
        raise ValueError("closes è vuoto.")

    if position_key_col not in ops_enriched.columns:
        raise ValueError(
            f"Colonna '{position_key_col}' non trovata "
            "in ops_enriched."
        )

    if ticker_col not in ops_enriched.columns:
        raise ValueError(
            f"Colonna '{ticker_col}' non trovata "
            "in ops_enriched."
        )

    # ========================================================
    # Frequenze supportate
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
    # Copie dati
    # ========================================================

    holdings = holdings.copy()
    closes = closes.copy()

    # ========================================================
    # Normalizzazione date
    # ========================================================

    holdings.index = pd.to_datetime(
        holdings.index,
        errors="coerce",
    )

    closes.index = pd.to_datetime(
        closes.index,
        errors="coerce",
    )

    holdings = (
        holdings.loc[
            ~holdings.index.isna()
        ]
        .sort_index()
    )

    closes = (
        closes.loc[
            ~closes.index.isna()
        ]
        .sort_index()
    )

    # ========================================================
    # PositionKey -> Ticker
    # ========================================================

    mapping_df = (
        ops_enriched[
            [position_key_col, ticker_col]
        ]
        .dropna()
        .drop_duplicates()
    )

    # Un PositionKey non deve appartenere
    # contemporaneamente a ticker diversi
    ticker_count = (
        mapping_df
        .groupby(position_key_col)[ticker_col]
        .nunique()
    )

    invalid_keys = ticker_count[
        ticker_count > 1
    ]

    if not invalid_keys.empty:
        raise ValueError(
            "Uno o più PositionKey risultano associati "
            "a ticker differenti."
        )

    position_to_ticker = (
        mapping_df
        .set_index(position_key_col)[ticker_col]
        .to_dict()
    )

    # ========================================================
    # Holdings può avere colonne int o string
    # ========================================================

    holdings_column_map = {
        str(column): column
        for column in holdings.columns
    }

    # ========================================================
    # Posizioni utilizzabili
    # ========================================================

    positions = []

    for position_key, ticker in position_to_ticker.items():

        key = str(position_key)

        if key not in holdings_column_map:
            continue

        if ticker not in closes.columns:
            raise ValueError(
                f"Prezzi mancanti per il ticker: {ticker}"
            )

        positions.append(
            {
                "position_key": position_key,
                "holdings_column": holdings_column_map[key],
                "ticker": ticker,
            }
        )

    if not positions:
        raise ValueError(
            "Nessuna posizione valida trovata."
        )

    positions = pd.DataFrame(positions)

    # ========================================================
    # Quantità storiche
    # ========================================================

    holding_columns = (
        positions["holdings_column"]
        .tolist()
    )

    quantities = (
        holdings[holding_columns]
        .apply(
            pd.to_numeric,
            errors="coerce",
        )
        .fillna(0.0)
    )

    # ========================================================
    # Prima data in cui TUTTE le posizioni sono attive
    #
    # In questo backtest interpretiamo "attiva"
    # come quantità > 0.
    # ========================================================

    all_active_mask = (
        quantities > 0
    ).all(axis=1)

    active_dates = quantities.index[
        all_active_mask
    ]

    if len(active_dates) == 0:
        raise ValueError(
            "Non esiste una data in cui tutte le "
            "posizioni siano contemporaneamente attive."
        )

    # ========================================================
    # Troviamo la prima data con:
    #
    # - tutte le posizioni attive
    # - tutti i prezzi disponibili e > 0
    # ========================================================

    tickers = (
        positions["ticker"]
        .drop_duplicates()
        .tolist()
    )

    candidate_dates = (
        active_dates
        .intersection(closes.index)
        .sort_values()
    )

    initial_date = None

    for date in candidate_dates:

        prices_day = pd.to_numeric(
            closes.loc[
                date,
                tickers,
            ],
            errors="coerce",
        )

        if (
            prices_day.notna().all()
            and np.isfinite(prices_day).all()
            and (prices_day > 0).all()
        ):
            initial_date = date
            break

    if initial_date is None:
        raise ValueError(
            "Nessuna data iniziale con quantità "
            "e prezzi validi per tutti i ticker."
        )

    # ========================================================
    # Quantità iniziali aggregate per ticker
    #
    # Questo gestisce anche il caso in cui più PositionKey
    # appartengano allo stesso ticker.
    # ========================================================

    initial_quantities = {}

    for _, position in positions.iterrows():

        ticker = position["ticker"]
        column = position["holdings_column"]

        quantity = pd.to_numeric(
            holdings.at[
                initial_date,
                column,
            ],
            errors="coerce",
        )

        if pd.isna(quantity):
            quantity = 0.0

        initial_quantities[ticker] = (
            initial_quantities.get(
                ticker,
                0.0,
            )
            + float(quantity)
        )

    initial_quantities = pd.Series(
        initial_quantities,
        dtype=float,
    )
