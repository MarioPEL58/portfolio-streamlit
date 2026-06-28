import pandas as pd

def ensure_datetime_series(obj, value_col=None, date_col="Data"):

    # ✅ Caso Series
    if isinstance(obj, pd.Series):
        s = obj.copy()

        # forza conversione index in datetime
        try:
            s.index = pd.to_datetime(s.index, errors="coerce")
        except Exception as e:
            print("Errore conversione index:", e)
            return None

        # rimuovi NaT
        s = s[~s.index.isna()]

        return s.sort_index()

    # ✅ Caso DataFrame
    elif isinstance(obj, pd.DataFrame):

        if date_col not in obj.columns:
            print(f"Colonna {date_col} non trovata")
            return None

        if value_col is None:
            print("value_col mancante per DataFrame")
            return None

        df = obj.copy()

        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])

        # ✅ groupby gestisce anche snapshot
        s = df.groupby(date_col)[value_col].sum()

        s = s[~s.index.isna()]

        return s.sort_index()

    # ✅ altro tipo → errore
    else:
        print("Tipo non supportato:", type(obj))
        return None
    return None
