import plotly.graph_objects as go
import plotly.express as px
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
        legend=dict(orientation="h"),
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
    if column not in exposure.columns:
        return None

    df = (
        exposure.groupby(column, dropna=False)["Valore"]
        .sum()
        .reset_index()
        .sort_values("Valore", ascending=False)
    )

    fig = px.bar(
        df,
        x=column,
        y="Valore",
        title=title if title else f"Allocazione per {column}"
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
            marker_color=df["color"],
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

def daily_pl_bar_chart_by_sign(current: pd.DataFrame, positive: bool = True, label_col: str = "Ticker"):
    if current is None or current.empty:
        return None

    df = current.copy()

    required_cols = ["P/L Giornaliero", "P/L Giornaliero %"]
    for col in required_cols:
        if col not in df.columns:
            return None

    df = df.dropna(subset=["P/L Giornaliero %"]).copy()

    if df.empty:
        return None

    if label_col not in df.columns:
        label_col = "Ticker" if "Ticker" in df.columns else df.columns[0]

    if positive:
        df = df[df["P/L Giornaliero %"] > 0].copy()
        title = "Posizioni in profitto giornaliero"
        color = "#26a69a"
        df = df.sort_values("P/L Giornaliero %", ascending=False)
        df["x_plot"] = df["P/L Giornaliero %"]
        df["label"] = df.apply(
            lambda x: f"{x['P/L Giornaliero %']:.2%} ({x['P/L Giornaliero']:.2f}€)",
            axis=1
        )
    else:
        df = df[df["P/L Giornaliero %"] < 0].copy()
        title = "Posizioni in perdita giornaliera"
        color = "#ef5350"
        df = df.sort_values("P/L Giornaliero %", ascending=True)

        # ✅ asse X positivo ma semanticamente negativo
        df["x_plot"] = df["P/L Giornaliero %"].abs()

        # label con segno negativo visibile
        df["label"] = df.apply(
            lambda x: f"{x['P/L Giornaliero %']:.2%} ({x['P/L Giornaliero']:.2f}€)",
            axis=1
        )

    if df.empty:
        return None

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df["x_plot"],
            y=df[label_col],
            orientation="h",
            marker_color=color,
            text=df["label"],
            textposition="outside",
            width=0.45  # ✅ barre più sottili
        )
    )

    # ✅ arrotondamento estremità (se supportato dalla tua versione Plotly)
    try:
        fig.update_traces(marker=dict(cornerradius=8))
    except Exception:
        pass

    max_x = df["x_plot"].max() if not df.empty else 0

    if positive:
        fig.update_layout(
            title=title,
            yaxis=dict(autorange="reversed"),
            xaxis=dict(
                tickformat=".2%"
            ),
            showlegend=False,
            margin=dict(l=20, r=20, t=50, b=20),
            height=max(300, 42 * len(df)),
            bargap=0.35
        )
    else:
        # ✅ tick negativi ma asse verso destra
        tickvals = [0]
        ticktext = ["0%"]

        if max_x > 0:
            steps = 4
            for i in range(1, steps + 1):
                v = max_x * i / steps
                tickvals.append(v)
                ticktext.append(f"-{v:.2%}")

        fig.update_layout(
            title=title,
            yaxis=dict(autorange="reversed"),
            xaxis=dict(
                tickmode="array",
                tickvals=tickvals,
                ticktext=ticktext,
                range=[0, max_x * 1.15 if max_x > 0 else 1]
            ),
            showlegend=False,
            margin=dict(l=20, r=20, t=50, b=20),
            height=max(300, 42 * len(df)),
            bargap=0.35
        )

    return fig
