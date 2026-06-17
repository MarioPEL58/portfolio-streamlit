import plotly.graph_objects as go
import plotly.express as px
from config import UI_CHART_STYLE as STYLE
from utils.i18n import t
from utils.display import get_display_columns
import pandas as pd

def portfolio_chart(series, bench_norm=None, benchmark_name=""):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=series.index,
        y=series["Valore portafoglio"],
        mode="lines",
        name="Valore portafoglio"
    ))

    fig.add_trace(go.Scatter(
        x=series.index,
        y=series["Capitale investito"],
        mode="lines",
        name="Capitale investito"
    ))

    fig.add_trace(go.Scatter(
        x=series.index,
        y=series["P/L trading"],
        mode="lines",
        name="P/L trading",
        yaxis="y2"
    ))

    if bench_norm is not None:
        fig.add_trace(go.Scatter(
            x=bench_norm.index,
            y=bench_norm.values,
            mode="lines",
            name=f"Benchmark: {benchmark_name}"
        ))

    fig.update_layout(
        height=540,
        xaxis_title="Data",
        yaxis_title="Euro",
        yaxis2=dict(
            title="P/L",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        legend=dict(orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=20, b=20)
    )

    return fig


def allocation_pie_chart(exposure, column="Ticker", title=None):
    
    if column not in exposure.columns:
        return None

    df = (
        exposure.groupby(column, dropna=False)["Valore"]
        .sum()
        .reset_index()
        .sort_values("Valore", ascending=False)
    )

    fig = px.pie(
        df,
        names=column,
        values="Valore",
        hole=0.45,
        title=title if title else f"Allocazione per {column}"
    )

    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=40, b=10)
    )

    return fig
    
def allocation_bar_chart(exposure, column="Area", title=None):
    
    def translate_tipo(val):
        key = f"type_{val}"
        return t(key) if t(key) != key else val
        
    if column not in exposure.columns:
        return None

    columns_map = get_display_columns()
    
    df = (
        exposure.groupby(column, dropna=False)["Valore"]
        .sum()
        .reset_index()
        .sort_values("Valore", ascending=False)
    )

    # ✅ QUI traduci i valori (solo per Tipo)
    if column == "Tipo":
        df[column] = df[column].astype(str).apply(
            lambda v: t(f"type_{v}") if t(f"type_{v}") != f"type_{v}" else v
        )

    # ✅ traduzione colonne
    column_label = columns_map.get(column, column)
    value_label = columns_map.get("Valore", "Valore")
    
   # ✅ rinomina dataframe per plotly
    df = df.rename(columns={
        column: column_label,
        "Valore": value_label
    })

    fig = px.bar(
        df,
        x=column_label,
        y=value_label,
        title=title if title else f"{t('allocation_title')} {column_label}"
    )

    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=40, b=10)
    )

    return fig

def daily_pl_bar_chart(current: pd.DataFrame, label_col: str = "Ticker"):
    if current is None or current.empty:
        return None

    df = current.copy()

    # sicurezza colonne
    required_cols = ["P/L Giornaliero", "P/L Giornaliero %"]
    for col in required_cols:
        if col not in df.columns:
            return None

    df = df.dropna(subset=["P/L Giornaliero %"])

    if df.empty:
        return None

    # label (usa Nome se disponibile)
    if label_col not in df.columns:
        label_col = "Ticker" if "Ticker" in df.columns else df.columns[0]

    # ordinamento per % decrescente
    df = df.sort_values("P/L Giornaliero %", ascending=False)

    # label combinata: % + €
    df["label"] = df.apply(
        lambda x: f"{x['P/L Giornaliero %']:.2%} ({x['P/L Giornaliero']:.2f}€)",
        axis=1
    )

    # colore
    df["color"] = df["P/L Giornaliero %"].apply(
        lambda x: "#26a69a" if x >= 0 else "#ef5350"
    )

    # costruzione grafico
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df["P/L Giornaliero %"],
            y=df[label_col],
            orientation="h",
            marker_color=dict(color= df["color"], cornerradius=8),
            text=df["label"],
            textposition="outside"
        )
    )

    fig.update_layout(
        title="Performance giornaliera (%)",
        yaxis=dict(autorange="reversed"),
        xaxis_tickformat=".2%",
        showlegend=False,
        margin=dict(l=20, r=20, t=50, b=20),
        height=max(350, 45 * len(df))
    )

    return fig

def daily_pl_bar_chart_by_sign(
    current: pd.DataFrame,
    positive: bool = True,
    label_col: str = "Ticker",
    pl_col: str = "P/L Giornaliero",
    pl_pct_col: str = "P/L Giornaliero %",
    max_abs_pct: float | None = None,
    top_n: int | None = None
):
    if current is None or current.empty:
        return None

    df = current.copy()

    required_cols = [pl_col, pl_pct_col]
    for col in required_cols:
        if col not in df.columns:
            return None

    df[pl_pct_col] = pd.to_numeric(df[pl_pct_col], errors="coerce")
    df[pl_col] = pd.to_numeric(df[pl_col], errors="coerce")
    df = df.dropna(subset=[pl_pct_col]).copy()

    if df.empty:
        return None

    if label_col not in df.columns:
        label_col = "Ticker" if "Ticker" in df.columns else df.columns[0]

    if positive:
        df = df[df[pl_pct_col] > 0].copy()
        df = df.sort_values(pl_pct_col, ascending=False)
        if top_n:
            df = df.head(top_n)
        df["x_plot"] = df[pl_pct_col]
        title = t("bar_profit")
        color = STYLE["color_positive"]
    else:
        df = df[df[pl_pct_col] < 0].copy()
        df = df.sort_values(pl_pct_col, ascending=True)
        if top_n:
            df = df.head(top_n)
        df["x_plot"] = df[pl_pct_col].abs()
        title = t("bar_loss")
        color = STYLE["color_negative"]

    if df.empty:
        return None

    # label breve: solo %
    df["label"] =df[pl_pct_col].apply(lambda x: f"{x:.2%}")
    if max_abs_pct is None:
        max_x = max(df["x_plot"].max(), 0.01)
    else:
        max_x = max(float(max_abs_pct), 0.01)

    # ✅ asse Y numerico
    n = len(df)
    y_pos = list(range(n))

    fig = go.Figure()

    # barra grigia di fondo
    fig.add_trace(
        go.Bar(
            x=[max_x] * n,
            y=y_pos,
            orientation="h",
            marker=dict(
                color=STYLE["color_background_bar"]
            ),
            showlegend=False,
            hoverinfo="skip",
            width=STYLE["bar_width"]
        )
    )

    # barra reale
    pl_pct_label = t("bar_pl_pct")
    pl_abs_label = t("bar_pl_abs")

    fig.add_trace(
        go.Bar(
            x=df["x_plot"],
            y=y_pos,
            orientation="h",
            base=0,
            marker=dict(
                color=color,
                cornerradius=STYLE["corner_radius"]
            ),
            text=df["label"],
            textposition="outside",
            customdata=df[[label_col, pl_pct_col, pl_col]],
            hovertemplate=(
                "%{customdata[0]}<br>"
                f"{pl_pct_label}: %{{customdata[1]:.4%}}<br>"
                f"{pl_abs_label}: %{{customdata[2]:.2f}}€"
                "<extra></extra>"
            ),
            width=STYLE["bar_width"]
        )
    )

    common_layout = dict(
        title=title,
        showlegend=False,
        height=max(STYLE["min_height"], STYLE["height_factor"] * n),
        margin=dict(l=20, r=20, t=50, b=20),
        bargap=STYLE["bargap"],
        barmode="overlay",
        yaxis=dict(
            tickmode="array",
            tickvals=y_pos,
            ticktext=df[label_col].tolist(),
            autorange="reversed"
        )
    )

    if positive:
        fig.update_layout(
            **common_layout,
            xaxis=dict(
                range=[0, max_x * STYLE["x_padding_factor"]],
                tickformat=".2%"
            )
        )
    else:
        tickvals = [0]
        ticktext = ["0%"]

        steps = 4
        for i in range(1, steps + 1):
            v = max_x * i / steps
            tickvals.append(v)
            ticktext.append(f"-{v:.2%}")

        fig.update_layout(
            **common_layout,
            xaxis=dict(
                range=[0, max_x * STYLE["x_padding_factor"]],
                tickmode="array",
                tickvals=tickvals,
                ticktext=ticktext
            )
        )

    return fig
