import numpy as np
import pandas as pd

# ==========================================================
# TREEMAP UTILITIES
# ==========================================================
def build_treemap_pl_customdata(
    df: pd.DataFrame,
    fig,
    pl_col: str,
    label_col: str,
):
    """
    Costruisce il customdata della Treemap
    contenente il P/L aggregato corretto per:

    - Portfolio
    - Intermediario
    - Tipo
    - Ticker

    indipendentemente dal numero di livelli
    presenti nella gerarchia Plotly.
    """

    # ==========================================================
    # AGGREGAZIONI
    # ==========================================================

    agg_portfolio = df[pl_col].sum()

    agg_interm = (
        df.groupby("Intermediario")[pl_col]
        .sum()
        .to_dict()
    )

    agg_tipo = (
        df.groupby(
            ["Intermediario", "Tipo"]
        )[pl_col]
        .sum()
        .to_dict()
    )

    # ==========================================================
    # FOGLIE
    # ==========================================================

    dict_foglie = {}

    for _, row in df.iterrows():

        key = (
            f"{row['Intermediario']}/"
            f"{row['Tipo']}/"
            f"{row[label_col]}"
        )

        dict_foglie[key] = row[pl_col]

    # ==========================================================
    # RICONOSCIMENTO GERARCHIA PLOTLY
    # ==========================================================

    plotly_ids = fig.data[0].ids

    has_portfolio_root = (
        df["Intermediario"].nunique() > 1
    )

    pl_allineato = []

    for node_id in plotly_ids:

        parts = node_id.split("/")

        # ======================================================
        # FOGLIA
        #
        # Usa sempre gli ultimi 3 livelli:
        # Intermediario / Tipo / Ticker
        # indipendentemente dai livelli superiori
        # ======================================================

        if len(parts) >= 3:

            lookup_key = "/".join(parts[-3:])

            if lookup_key in dict_foglie:

                pl_allineato.append(
                    dict_foglie[lookup_key]
                )

                continue

        # ======================================================
        # PORTAFOGLIO
        # ======================================================

        if has_portfolio_root and len(parts) == 1:

            pl_allineato.append(
                agg_portfolio
            )

        # ======================================================
        # INTERMEDIARIO
        # ======================================================

        elif (
            (not has_portfolio_root and len(parts) == 1)
            or
            (has_portfolio_root and len(parts) == 2)
        ):

            intermediario = parts[-1]

            pl_allineato.append(
                agg_interm.get(
                    intermediario,
                    0.0
                )
            )

        # ======================================================
        # TIPO
        # ======================================================

        elif (
            (not has_portfolio_root and len(parts) == 2)
            or
            (has_portfolio_root and len(parts) == 3)
        ):

            intermediario = parts[-2]
            tipo = parts[-1]

            pl_allineato.append(
                agg_tipo.get(
                    (intermediario, tipo),
                    0.0
                )
            )

        # ======================================================
        # DEFAULT
        # ======================================================

        else:

            pl_allineato.append(0.0)

    # ==========================================================
    # CUSTOMDATA ALLINEATO AGLI ID PLOTLY
    # ==========================================================

    return (
        np.array(pl_allineato)
        .reshape(-1, 1)
    )

def get_treemap_path(
    df: pd.DataFrame,
    label_col: str,
    portfolio_label: str,
):
    """
    Costruisce dinamicamente il path
    della Treemap.

    Se esiste un solo intermediario:

        Intermediario
            ↓
            Tipo
                ↓
                Ticker

    Se esistono più intermediari:

        Portafoglio
            ↓
            Intermediario
                ↓
                Tipo
                    ↓
                    Ticker
    """

    if df["Intermediario"].nunique() > 1:

        df["Portfolio"] = portfolio_label

        return [
            "Portfolio",
            "Intermediario",
            "Tipo",
            label_col,
        ]

    return [
        "Intermediario",
        "Tipo",
        label_col,
    ]
