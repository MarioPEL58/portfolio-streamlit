import plotly.graph_objects as go
import plotly.express as px
from config import UI_CHART_STYLE as STYLE
import numpy as np
from utils.i18n import t
from utils.display import get_display_columns
import pandas as pd

def portfolio_chart(series, bench_norm=None, benchmark_name=""):

    columns_map = get_display_columns()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=series.index,
        y=series["Valore portafoglio"],
        mode="lines",
        name=columns_map.get("Valore portafoglio", "Portfolio value")
    ))

    fig.add_trace(go.Scatter(
        x=series.index,
        y=series["Capitale investito"],
        mode="lines",
        name=columns_map.get("Capitale investito", "Invested capital")
    ))

    fig.add_trace(go.Scatter(
        x=series.index,
        y=series["P/L trading"],
        mode="lines",
        name=columns_map.get("P/L trading", "Trading P/L"),
        yaxis="y2"
    ))

    if bench_norm is not None:
        fig.add_trace(go.Scatter(
            x=bench_norm.index,
            y=bench_norm.values,
            mode="lines",
            name=f"{t('benchmark_label')}: {benchmark_name}"
        ))

    fig.update_layout(
        height=540,
        xaxis_title=t("col_date"),
        yaxis_title=t("currency_label"),
        yaxis2=dict(
            title=t("pl_label"),
            overlaying="y",
            side="right",
            showgrid=False
        ),
        legend=dict(
            orientation="h",
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

def sharpe_gauge(sharpe_value: float | None):

    if sharpe_value is None:
        return None

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sharpe_value,
        number={'suffix': ""},

        title={'text': "Sharpe Ratio"},

        gauge={
            'axis': {'range': [0, 3]},
            'bar': {'color': "black"},  # ✅ pallino/indicatore

            'steps': [
                {'range': [0, 1], 'color': "#ef5350"},   # rosso
                {'range': [1, 2], 'color': "#fdd835"},   # giallo
                {'range': [2, 3], 'color': "#66bb6a"},   # verde
            ],

            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 1.0,
                'value': sharpe_value
            }
        }
    ))

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig

# =========================
# ✅ helpers colore
# =========================
def _interp_color(c1, c2, x):
    return (
        int(c1[0] + (c2[0] - c1[0]) * x),
        int(c1[1] + (c2[1] - c1[1]) * x),
        int(c1[2] + (c2[2] - c1[2]) * x),
    )


def _rgb_str(rgb):
    return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"


# =========================
# ✅ funzione principale
# =========================
def sharpe_bar_gradient(sharpe_value: float | None, x_max: float = 3.0):

    if sharpe_value is None:
        return None

    # clamp visuale
    x_val = max(0, min(sharpe_value, x_max))

    fig = go.Figure()

    # dimensioni barra
    y_center = 0
    height = 0.4
    radius = height / 2

    # colore base
    red = (239, 83, 80)      # #ef5350
    yellow = (253, 216, 53)  # #fdd835
    green = (102, 187, 106)  # #66bb6a

    # =========================
    # ✅ gradiente interpolato
    # =========================
    steps = 120
    xs = np.linspace(0, x_max, steps + 1)

    for i in range(steps):
        x0 = xs[i]
        x1 = xs[i + 1]
        mid = (x0 + x1) / 2

        # rosso → giallo → verde
        if mid <= x_max / 2:
            alpha = mid / (x_max / 2)
            color = _rgb_str(_interp_color(red, yellow, alpha))
        else:
            alpha = (mid - x_max / 2) / (x_max / 2)
            color = _rgb_str(_interp_color(yellow, green, alpha))

        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x1,
            y0=y_center - radius,
            y1=y_center + radius,
            fillcolor=color,
            line=dict(width=0),
            layer="below"
        )

    # =========================
    # ✅ estremità arrotondate (pill)
    # =========================
    fig.add_shape(
        type="circle",
        x0=0 - radius,
        x1=0 + radius,
        y0=y_center - radius,
        y1=y_center + radius,
        fillcolor=_rgb_str(red),
        line=dict(width=0),
        layer="below"
    )

    fig.add_shape(
        type="circle",
        x0=x_max - radius,
        x1=x_max + radius,
        y0=y_center - radius,
        y1=y_center + radius,
        fillcolor=_rgb_str(green),
        line=dict(width=0),
        layer="below"
    )

    # =========================
    # ✅ indicatore (pallino)
    # =========================
    fig.add_trace(go.Scatter(
        x=[x_val],
        y=[y_center],
        mode="markers+text",
        marker=dict(
            color="black",
            size=14
        ),
        text=[f"{sharpe_value:.2f}"],
        textposition="top center",
        showlegend=False,
        hovertemplate=f"{t('sharpe_value')}: {sharpe_value:.2f}<extra></extra>"
    ))

    # =========================
    # ✅ layout
    # =========================
    fig.update_layout(
        height=170,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(
            range=[0, x_max],
            tickmode="array",
            tickvals=[0, 1, 2, 3],
            title=t("sharpe_value"),
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            range=[-1, 1],
            showticklabels=False,
            showgrid=False,
            zeroline=False
        ),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    return fig
