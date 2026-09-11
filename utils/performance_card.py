import pandas as pd
import streamlit as st
from utils.formatting import fmt_pct


def render_performance_card(value, label):

    if value is None:
        pct_text = "—"
        positive = True
    else:
        pct_text = fmt_pct(value)
        positive = value >= 0

    text_color = "#14c8b8" if positive else "#ff4d67"

    bg_color = (
        "linear-gradient(135deg, #031b1a 0%, #0d4c44 100%)"
        if positive
        else
        "linear-gradient(135deg, #5a1f24 0%, #72292f 100%)"
    )

    st.markdown(
        f"""
        <div style="
            padding:16px;
            border-radius:12px;
            background:{bg_color};
            text-align:center;
            min-height:90px;
            display:flex;
            flex-direction:column;
            justify-content:center;
        ">
            <div style="
                color:{text_color};
                font-size:1.6rem;
                font-weight:700;
            ">
                {pct_text}
            </div>
            <div style="
                color:#d0d0d0;
                font-size:1.2rem;
                font-weight:600;
            ">
                {label}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
def render_performance_cards_tot(ts: pd.DataFrame):
    
    # st.write(ts.columns.tolist()) # DEBUG
    cards = [
        ("P/L Totale Giornaliero %", "1D"),
        ("P/L Totale 7 Giorni %", "1W"),
        ("P/L Totale 30 Giorni %", "1M"),
        ("Performance 3M %", "3M"),
        ("Performance 6M %", "6M"),
        ("Performance YTD %", "YTD"),
        ("Performance 1Y %", "1Y"),
    ]

    cols = st.columns(len(cards))

    for col, (column_name, label) in zip(cols, cards):
    
        series = ts[column_name].dropna()
    
        if series.empty:
            value = None
        else:
            value = float(series.iloc[-1])
    
        with col:
            render_performance_card(value, label)

def render_performance_cards(current):

    open_value = float(current["Valore"].sum())

    cards = [
        (
            current["P/L Giornaliero"].sum() /
            (open_value - current["P/L Giornaliero"].sum()),
            "1D"
        ),
        (
            current["P/L 7 Giorni"].sum() /
            (open_value - current["P/L 7 Giorni"].sum()),
            "1W"
        ),
        (
            current["P/L 30 Giorni"].sum() /
            (open_value - current["P/L 30 Giorni"].sum()),
            "1M"
        ),
    ]

    cols = st.columns(len(cards))

    for col, (value, label) in zip(cols, cards):
        with col:
            render_performance_card(value, label)
