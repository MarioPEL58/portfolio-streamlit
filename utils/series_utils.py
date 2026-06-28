import pandas as pd

def ensure_datetime_series(series_or_df, value_col=None, date_col="Data"):

    # Caso 1: è già una Series
    if isinstance(series_or_df, pd.Series):
        s = series_or_df.copy()

        if not isinstance(s.index, pd.DatetimeIndex):
            try:
                s.index = pd.to_datetime(s.index, errors="coerce")
            except:
                return None

        return s.sort_index()

    # Caso 2: è un DataFrame
    df = series_or_df.copy()

    # Se Data esiste → usala
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])

        if value_col is None:
            raise ValueError("Serve value_col per DataFrame")

        # ✅ gestisce anche snapshot (groupby)
        s = df.groupby(date_col)[value_col].sum()

        return s.sort_index()

    return None
