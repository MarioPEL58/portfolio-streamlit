import plotly.graph_objects as go


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
        y=series["P/L totale"],
        mode="lines",
        name="P/L totale",
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
