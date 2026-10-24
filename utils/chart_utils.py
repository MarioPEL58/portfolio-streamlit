import numpy as np
import pandas as pd

def build_treemap_pl_customdata(
    df: pd.DataFrame,
    fig,
    pl_col: str,
    label_col: str,
):
    """
    Costruisce il customdata per la Treemap
    contenente il P/L aggregato corretto per:

    - Portafoglio
    - Intermediario
    - Tipo
    - Ticker

    mantenendo il layout nativo di Plotly.
    """

    # ==========================================================
    # AGGREGAZIONI
    # ==========================================================

    # P/L totale del portafoglio
    agg_portfolio = df[pl_col].sum()

    # P/L per intermediario
    agg_interm = (
        df.groupby("Intermediario")[pl_col]
          .sum()
          .to_dict()
    )

    # P/L per tipo all'interno dell'intermediario
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

    # Dizionario dei ticker
    # Chiave:
    # Intermediario/Tipo/Ticker
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

    # Se esiste più di un intermediario
    # abbiamo aggiunto una radice "Portfolio"
    has_portfolio_root = (
        df["Intermediario"].nunique() > 1
    )

    pl_allineato = []

    for node_id in plotly_ids:

        parts = node_id.split("/")

        # ======================================================
        # CON RADICE PORTAFOGLIO
        # ======================================================

        if has_portfolio_root:

            if len(parts) == 1:

                # Portfolio
                pl_allineato.append(
                    agg_portfolio
                )

            elif len(parts) == 2:

                # Intermediario
                pl_allineato.append(
                    agg_interm.get(
                        parts[1],
                        0.0
                    )
                )

            elif len(parts) == 3:

                # Tipo
                pl_allineato.append(
                    agg_tipo.get(
                        (parts[1], parts[2]),
                        0.0
                    )
                )

            elif len(parts) == 4:

                # Ticker
                pl_allineato.append(
                    dict_foglie.get(
                        node_id,
                        0.0
                    )
                )

            else:

                pl_allineato.append(0.0)

        # ======================================================
        # SENZA RADICE PORTAFOGLIO
        # ======================================================

        else:

            if len(parts) == 1:

                # Intermediario
                pl_allineato.append(
                    agg_interm.get(
                        parts[0],
                        0.0
                    )
                )

            elif len(parts) == 2:

                # Tipo
                pl_allineato.append(
                    agg_tipo.get(
                        (parts[0], parts[1]),
                        0.0
                    )
                )

            elif len(parts) == 3:

                # Ticker
                pl_allineato.append(
                    dict_foglie.get(
                        node_id,
                        0.0
                    )
                )

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
    label_col: str
):

    if df["Intermediario"].nunique() > 1:

        df["Portfolio"] = t("portfolio")

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
