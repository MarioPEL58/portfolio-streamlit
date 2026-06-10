import plotly.graph_objects as go
import plotly.express as px

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
