import plotly.graph_objects as go
import plotly.express as px
from config import UI_CHART_STYLE as STYLE
import numpy as np
from utils.i18n import t
from utils.display import get_display_columns
import pandas as pd

def portfolio_chart(series, bench_norm=None, benchmark_name="", note_text=None):

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
    
    COLORE_ASSE_DESTRO = "#D63384" # Rosa scuro/intenso, perfetto sia su scuro che su bianco
    fig.add_trace(go.Scatter(
        x=series.index,
        y=series["P/L trading"],
        mode="lines",
        name=columns_map.get("P/L trading", "Trading P/L"),
        yaxis="y2",
        line=dict(color=COLORE_ASSE_DESTRO, width=2) # 🔹 Linea ugule a colore asse 
    ))

    if bench_norm is not None:
        fig.add_trace(go.Scatter(
            x=bench_norm.index,
            y=bench_norm.values,
            mode="lines",
            name=f"{t('benchmark_label')}: {benchmark_name}"
        ))

    # ✅ Nota dati di mercato
    if note_text:
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.01,
            y=0.02,
            text=f"<i>{note_text}</i>",
            showarrow=False,
            font=dict(size=11, color="gray"),
            align="left"
        )
        
    fig.update_layout(
        height=540,
        xaxis_title=t("col_date"),
        yaxis_title=t("currency_label"),
        xaxis=dict(
            title=dict(standoff=15), # Allontana la scritta "Data" dalle date sotto
            automargin=True
        ),
        yaxis=dict(
            title=dict(standoff=15), # Allontana la scritta "Euro" dai numeri a sinistra
            automargin=True
        ),
        yaxis2=dict(
            title=dict(text=t("pl_label"), standoff=15,font=dict(color=COLORE_ASSE_DESTRO) ), # colore titolo
            tickfont=dict(color=COLORE_ASSE_DESTRO),  # Numeri dell'asse destro
            overlaying="y",
            side="right",
            showgrid=False,
            automargin=True
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=80, r=80, t=20, b=60)
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

    x_val = max(0, min(sharpe_value, x_max))

    fig = go.Figure()

    y_center = 0
    half_height = 0.2

    red = (239, 83, 80)
    yellow = (253, 216, 53)
    green = (102, 187, 106)

    # =========================
    # ✅ gradiente (STABILE)
    # =========================
    steps = 100
    xs = np.linspace(0, x_max, steps + 1)

    for i in range(steps):
        x0 = xs[i]
        x1 = xs[i + 1]
        mid = (x0 + x1) / 2

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
            y0=y_center - half_height,
            y1=y_center + half_height,
            fillcolor=color,
            line=dict(width=0),
            layer="below"   # ✅ IMPORTANTISSIMO
        )

    # =========================
    # ✅ PALLINO (SOPRA)
    # =========================
    fig.add_trace(go.Scatter(
        x=[x_val],
        y=[y_center],
        mode="markers",
        marker=dict(
            color="black",
            size=14,
            line=dict(color="white", width=1)
        ),
        showlegend=False,
        hovertemplate=f"{t('sharpe_value')}: {sharpe_value:.2f}<extra></extra>"
    ))

    # =========================
    # ✅ LABEL SOPRA
    # =========================
    fig.add_annotation(
        x=x_val,
        y=y_center + half_height + 0.12,
        text=f"{sharpe_value:.2f}",
        showarrow=False,
        font=dict(color="white", size=12),
        xanchor="center",
        yanchor="bottom"
    )

    # =========================
    # ✅ ASSE X SEMPLICE (fix stabile)
    # =========================
    fig.update_layout(
        height=100,
        margin=dict(l=20, r=20, t=10, b=5),

        plot_bgcolor="#0E1117",
        paper_bgcolor="#0E1117",

        xaxis=dict(
            range=[0, x_max],
            showgrid=False,
            zeroline=False,
            tickmode="array",
            tickvals=[0, x_max],
            ticktext=["0", str(int(x_max))],
            tickfont=dict(color="white"),
            side="bottom"
        ),

        yaxis=dict(
            range=[-0.4, 0.5],
            showticklabels=False,
            showgrid=False,
            zeroline=False
        )
    )

    return fig

# =========================
# ✅ funzione generica
# =========================
def ratio_bar_gradient(
    value: float | None,
    title: str,
    x_max: float = 3.0,
    tick_vals: list[float] | None = None,
    tick_text: list[str] | None = None,
):
    if value is None:
        return None

    x_val = max(0, min(value, x_max))

    fig = go.Figure()

    y_center = 0
    half_height = 0.2

    red = (239, 83, 80)
    yellow = (253, 216, 53)
    green = (102, 187, 106)

    # =========================
    # ✅ gradiente
    # =========================
    steps = 100
    xs = np.linspace(0, x_max, steps + 1)

    for i in range(steps):
        x0 = xs[i]
        x1 = xs[i + 1]
        mid = (x0 + x1) / 2

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
            y0=y_center - half_height,
            y1=y_center + half_height,
            fillcolor=color,
            line=dict(width=0),
            layer="below"
        )

    # =========================
    # ✅ marker
    # =========================
    fig.add_trace(go.Scatter(
        x=[x_val],
        y=[y_center],
        mode="markers",
        marker=dict(
            color="black",
            size=14,
            line=dict(color="white", width=1)
        ),
        showlegend=False,
        hovertemplate=f"{title}: {value:.2f}<extra></extra>"
    ))

    # =========================
    # ✅ label sopra
    # =========================
    fig.add_annotation(
        x=x_val,
        y=y_center + half_height + 0.12,
        text=f"{value:.2f}",
        showarrow=False,
        font=dict(color="white", size=12),
        xanchor="center",
        yanchor="bottom"
    )

    # =========================
    # ✅ ticks asse x
    # =========================
    if tick_vals is None:
        tick_vals = [0, x_max]

    if tick_text is None:
        tick_text = [str(v).rstrip("0").rstrip(".") for v in tick_vals]

    fig.update_layout(
        height=100,
        margin=dict(l=20, r=20, t=10, b=5),
        plot_bgcolor="#0E1117",
        paper_bgcolor="#0E1117",
        xaxis=dict(
            range=[0, x_max],
            showgrid=False,
            zeroline=False,
            tickmode="array",
            tickvals=tick_vals,
            ticktext=tick_text,
            tickfont=dict(color="white")
        ),
        yaxis=dict(
            range=[-0.45, 0.55],
            showticklabels=False,
            showgrid=False,
            zeroline=False
        )
    )

    return fig

def ratio_bar_gradient_compare(
    portfolio_value: float | None,
    benchmark_value: float | None,
    title: str,
    x_max: float = 3.0,
    mode: str = "gradient"   # ✅ nuovo parametro
):
    if portfolio_value is None:
        return None

    fig = go.Figure()

    y_center = 0
    half_height = 0.2

    red = (239, 83, 80)
    yellow = (253, 216, 53)
    green = (102, 187, 106)

    steps = 100
    xs = np.linspace(0, x_max, steps + 1)

    # =========================
    # ✅ BARRA
    # =========================
    if mode == "gradient":

        for i in range(steps):
            x0 = xs[i]
            x1 = xs[i + 1]
            mid = (x0 + x1) / 2

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
                y0=y_center - half_height,
                y1=y_center + half_height,
                fillcolor=color,
                line=dict(width=0),
                layer="below"
            )

    elif mode == "gray":

        for i in range(steps):
            fig.add_shape(
                type="rect",
                x0=xs[i],
                x1=xs[i + 1],
                y0=y_center - half_height,
                y1=y_center + half_height,
                fillcolor="rgba(200,200,200,0.2)",
                line=dict(width=0),
                layer="below"
            )

        # ✅ linea benchmark a 1
        fig.add_shape(
            type="line",
            x0=1,
            x1=1,
            y0=y_center - half_height - 0.05,
            y1=y_center + half_height + 0.05,
            line=dict(color="white", width=1, dash="dot"),
            layer="below"
        )

    # =========================
    # ✅ clamp
    # =========================
    def clamp(v):
        return max(0, min(v, x_max))

    p_val = clamp(portfolio_value)

    # =========================
    # ✅ MARKER PORTFOLIO
    # =========================
    fig.add_trace(go.Scatter(
        x=[p_val],
        y=[y_center],
        mode="markers",
        marker=dict(
            color="black",
            size=14,
            line=dict(color="white", width=1)
        ),
        name="Portfolio",
        showlegend=True
    ))

    fig.add_annotation(
        x=p_val,
        y=y_center + half_height + 0.12,
        text=f"{portfolio_value:.2f}",
        showarrow=False,
        font=dict(color="white", size=12),
        xanchor="center",
        yanchor="bottom"
    )

    # =========================
    # ✅ MARKER BENCHMARK
    # =========================
    if benchmark_value is not None:
        b_val = clamp(benchmark_value)
        
        if mode == "gray":
            bench_text = t("beta_market_label")
        else:
            bench_text = f"{benchmark_value:.2f}"
            
        fig.add_trace(go.Scatter(
            x=[b_val],
            y=[y_center],
            mode="markers",
            marker=dict(
                color="white",
                size=12,
                line=dict(color="black", width=1)
            ),
            name="Benchmark",
            showlegend=True
        ))

        fig.add_annotation(
            x=b_val,
            y=y_center - half_height - 0.12,
            text=bench_text,
            showarrow=False,
            font=dict(color="white", size=11),
            xanchor="center",
            yanchor="top"
        )

    # =========================
    # ✅ LAYOUT
    # =========================
    fig.update_layout(
        height=120,
        margin=dict(l=20, r=20, t=10, b=5),
        plot_bgcolor="#0E1117",
        paper_bgcolor="#0E1117",
        xaxis=dict(
            range=[0, x_max],
            showgrid=False,
            zeroline=False,
            tickmode="array",
            tickvals=[0, x_max],
            ticktext=["0", str(int(x_max))],
            tickfont=dict(color="white")
        ),
        yaxis=dict(
            range=[-0.6, 0.6],
            showticklabels=False,
            showgrid=False,
            zeroline=False
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=1,
            font=dict(color="white")
        )
    )

    return fig

# def daily_pl_treemap(current: pd.DataFrame, label_col="Ticker"):

#     if current is None or current.empty:
#         return None

#     df = current.copy()

#     required = ["Valore", "P/L Giornaliero %", "P/L Giornaliero", "Intermediario"]
#     for col in required:
#         if col not in df.columns:
#             return None

#     df = df.dropna(subset=["Valore", "P/L Giornaliero %"]).copy()

#     if label_col not in df.columns:
#         label_col = "Ticker"

#     df["color_val"] = df["P/L Giornaliero %"]

#     # ✅ LABEL SU DUE RIGHE
#     df["label_full"] = df.apply(
#         lambda row: f"{row[label_col]}<br>{row['P/L Giornaliero']:+.0f}€",
#         axis=1
#     )

#     max_abs = df["color_val"].abs().max()

#     fig = px.treemap(
#         df,
#         path=["Intermediario", "label_full"],
#         values="Valore",
#         color="color_val",
#         color_continuous_scale=[
#             (0.0, "#5a0000"),
#             (0.25, "#d73027"),
#             (0.5, "#2b2b2b"),   # neutro tipo finviz
#             (0.75, "#1a9850"),
#             (1.0, "#00441b")
#         ],
#         range_color=[-max_abs, max_abs]
#     )

#     # ✅ TESTO CENTRATO
#     fig.update_traces(
#         textinfo="label",
#         textposition="middle center"
#     )

#     # hover
#     fig.update_traces(
#         hovertemplate=
#         "<b>%{label}</b><br>" +
#         "Intermediario: %{parent}<br>" +
#         "Valore: %{value:.2f}€<br>" +
#         "P/L giornaliero: %{customdata.2f}€<br>" +
#         "P/L %: %{color:.2%}<extra></extra>",
#         customdata=df[["P/L Giornaliero"]]
#     )

#     fig.update_layout(
#         margin=dict(t=10, l=10, r=10, b=10),
#         coloraxis_colorbar=dict(title="P/L %")
#     )

#     return fig

import plotly.express as px

def daily_pl_treemap(current: pd.DataFrame, label_col="Ticker"):

    if current is None or current.empty:
        return None

    df = current.copy()

    # =========================
    # colonne necessarie
    # =========================
    required = ["Valore", "P/L Giornaliero %", "P/L Giornaliero", "Intermediario", "Tipo"]
    for col in required:
        if col not in df.columns:
            return None

    # =========================
    # pulizia dati
    # =========================
    df = df.dropna(subset=["Valore", "P/L Giornaliero %"]).copy()

    # fallback label
    if label_col not in df.columns:
        label_col = "Ticker"

    # =========================
    # colore = rendimento ticker (SOLO quello)
    # =========================
    df["color_val"] = df["P/L Giornaliero %"]

    # =========================
    # label multiline centrata
    # =========================
    df["label_full"] = df.apply(
        lambda row: f"{row[label_col]}<br>{row['P/L Giornaliero']:+.0f}€",
        axis=1
    )

    # =========================
    # scala simmetrica (centro 0)
    # =========================
    max_abs = df["color_val"].abs().max()

    # =========================
    # TREEMAP: Intermediario → Tipo → Ticker
    # =========================
    fig = px.treemap(
        df,
        path=["Intermediario", "Tipo", "label_full"],
        values="Valore",
        color="color_val",
        color_continuous_scale=[
            (0.0, "#5a0000"),   # rosso scuro
            (0.25, "#d73027"),  # rosso
            (0.5, "#2b2b2b"),   # neutro finviz
            (0.75, "#1a9850"),  # verde
            (1.0, "#00441b")    # verde scuro
        ],
        range_color=[-max_abs, max_abs]
    )

    # =========================
    # bordo nero stile finviz
    # =========================
    fig.update_traces(
        marker=dict(
            line=dict(color="black", width=1.2)
        ),
        textinfo="label",
        textposition="middle center"
    )

    # =========================
    # hover
    # =========================
    fig.update_traces(
        hovertemplate=
        "<b>%{label}</b><br>" +
        "Intermediario: %{parent}<br>" +
        "Valore: %{value:.2f}€<br>" +
        "P/L giornaliero: %{customdata[0]:.2f}€<br>" +
        "P/L %: %{color:.2%}" +
        "<extra></extra>",
        customdata=df[["P/L Giornaliero"]]
    )

    # =========================
    # layout pulito (senza titolo)
    # =========================
    fig.update_layout(
        margin=dict(t=10, l=10, r=10, b=10),
        coloraxis_colorbar=dict(title="P/L %")
    )

    return fig

def pl_treemap(
    current: pd.DataFrame,
    label_col: str = "Ticker",
    pl_mode: str = "daily"
):

    if current is None or current.empty:
        return None

    df = current.copy()

    # =========================
    # mapping colonne robusto
    # =========================
    if pl_mode == "total":
        pl_col = "P/L"
        pl_pct_col = "P/L %"
    else:
        pl_col = "P/L Giornaliero"
        pl_pct_col = "P/L Giornaliero %"

    required = ["Valore", pl_pct_col, pl_col, "Intermediario", "Tipo"]
    for col in required:
        if col not in df.columns:
            return None

    df = df.dropna(subset=["Valore", pl_pct_col]).copy()

    if label_col not in df.columns:
        label_col = "Ticker"

    # =========================
    # colore = rendimento
    # =========================
    df["color_val"] = df[pl_pct_col]

    # =========================
    # ✅ LABEL CON € + %
    # =========================
    df["label_full"] = df.apply(
        lambda row: (
            f"{row[label_col]}"
            f"<br>{row[pl_col]:+.0f}€ | {row[pl_pct_col]:+.2%}"
        ),
        axis=1
    )

    # =========================
    # scala simmetrica
    # =========================
    max_abs = df["color_val"].abs().max()

    # =========================
    # TREEMAP
    # =========================
    fig = px.treemap(
        df,
        path=["Intermediario", "Tipo", "label_full"],
        values="Valore",
        color="color_val",
        color_continuous_scale = [
            (0.0,  "#F23636"),  # rosso acceso
            (0.16, "#B53C3C"),  # rosso mattone
            (0.33, "#7E3E47"),  # rosso bordeaux
            (0.5,  "#3F4350"),  # grigio neutro
            (0.66, "#2E6C4A"),  # verde scuro
            (0.83, "#289F51"),  # verde medio
            (1.0,  "#23CE5F")   # verde acceso
        ],
        range_color=[-max_abs, max_abs]
    )

    # =========================
    # stile
    # =========================
    fig.update_traces(
        marker=dict(line=dict(color="black", width=1.2)),
        textinfo="label",
        textposition="middle center"
    )

    # =========================
    # hover
    # =========================
    fig.update_traces(
        hovertemplate=
        "<b>%{label}</b><br>" +
        "Intermediario: %{parent}<br>" +
        "Valore: %{value:.2f}€<br>" +
        f"P/L: %{{customdata.2f}}€<br>" +
        f"P/L %: %{{color:.2%}}<extra></extra>",
        customdata=df[[pl_col]]
    )

    # =========================
    # layout
    # =========================
    fig.update_layout(
        margin=dict(t=10, l=10, r=10, b=10),
        coloraxis_colorbar=dict(title=pl_pct_col, tickformat=".0%")
    )

    return fig
