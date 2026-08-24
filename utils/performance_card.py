import streamlit as st
from utils.formatting import fmt_pct


def render_performance_card(value, label):
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
                font-size:2rem;
                font-weight:700;
            ">
                {fmt_pct(value)}
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
    
def render_performance_cards(ts: pd.DataFrame):

    cards = [
        ("P/L Giornaliero %", "1D"),
        ("P/L 7 Giorni %", "1W"),
        ("P/L 30 Giorni %", "1M"),
    ]

    cols = st.columns(len(cards))

    for col, (column_name, label) in zip(cols, cards):

        value = (
            ts[column_name]
            .dropna()
            .iloc[-1]
            * 100
        )

        with col:
            render_performance_card(value, label)
