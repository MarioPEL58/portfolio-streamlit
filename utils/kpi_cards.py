import streamlit as st
from utils.formatting import fmt_eur, fmt_pct


# =========================
# 1️⃣ VALORE PORTAFOGLIO
# =========================
def render_value_card(value):
    st.markdown(
        f"""
        <div style="
            padding: 16px;
            border-radius: 12px;
            background-color: #1f1f1f;
            border: 1px solid #2a2a2a;
        ">
            <div style="color: #9aa0a6; font-size: 0.9em;">
                Valore del portafoglio
            </div>
            <div style="
                font-size: 1.8em;
                font-weight: 600;
                margin-top: 4px;
            ">
                {fmt_eur(value)}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# 2️⃣ NON REALIZZATO
# =========================
def render_unrealized_card(value, pct, daily_value=None, daily_pct=None):

    color = "#26a69a" if value >= 0 else "#ef5350"
    pct_color = "#26a69a" if pct >= 0 else "#ef5350"

    daily_color = "#26a69a" if (daily_value is not None and daily_value >= 0) else "#ef5350"
    daily_pct_color = "#26a69a" if (daily_pct is not None and daily_pct >= 0) else "#ef5350"

    st.markdown(
        f"""
        <div style="
            padding: 16px;
            border-radius: 12px;
            background-color: #1f1f1f;
            border: 1px solid #2a2a2a;
        ">
            <div style="color: #9aa0a6; font-size: 0.9em;">
                Profitto non realizzato
            </div>
            <div style="
                margin-top: 6px;
                font-size: 1.8em;
                font-weight: 600;
                color: {color};
            ">
                {fmt_eur(value)}
                <span style="font-size: 0.6em; margin-left: 8px; color: {pct_color};">
                    {fmt_pct(pct)}
                </span>
            </div>
            <div style="
                margin-top: 10px;
                font-size: 0.85em;
                color: #9aa0a6;
                display: flex;
                justify-content: space-between;
            ">
                <span>Ultimo giorno</span>
                <span>
                    <span style="color: {daily_color};">
                        {fmt_eur(daily_value) if daily_value is not None else ""}
                    </span>
                    <span style="margin-left: 6px; color: {daily_pct_color};">
                        {fmt_pct(daily_pct) if daily_pct is not None else ""}
                    </span>
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# 3️⃣ REALIZZATO
# =========================
def render_realized_card(realized_total, dividends_total):

    color = "#26a69a" if realized_total >= 0 else "#ef5350"
    div_color = "#26a69a" if dividends_total >= 0 else "#ef5350"

    st.markdown(
        f"""
        <div style="
            padding: 16px;
            border-radius: 12px;
            background-color: #1f1f1f;
            border: 1px solid #2a2a2a;
        ">
            <div style="color: #9aa0a6; font-size: 0.9em;">
                Profitto realizzato
            </div>
            <div style="
                margin-top: 6px;
                display: flex;
                align-items: baseline;
                gap: 6px;
                color: {color};
            ">
                <span style="font-size: 1.8em; font-weight: 600;">
                    {fmt_eur(realized_total)}
                </span>
                <span style="font-size: 0.7em;">
                    EUR
                </span>
            </div>
            <div style="
                margin-top: 10px;
                font-size: 0.85em;
                color: #9aa0a6;
                display: flex;
                justify-content: space-between;
            ">
                <span>Dividendi totali</span>
                <span style="color: {div_color};">
                    {fmt_eur(dividends_total)}
                    <span style="font-size: 0.9em;"> EUR</span>
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# 4️⃣ TOTALE
# =========================
def render_total_pl_card(total_pl, total_pct, annualized_pct=None):

    color = "#26a69a" if total_pl >= 0 else "#ef5350"
    pct_color = "#26a69a" if total_pct >= 0 else "#ef5350"

    st.markdown(
        f"""
        <div style="
            padding: 16px;
            border-radius: 12px;
            background-color: #1f1f1f;
            border: 1px solid #2a2a2a;
        ">
            <div style="color: #9aa0a6; font-size: 0.9em;">
                Profitto totale
            </div>
            <div style="
                margin-top: 6px;
                display: flex;
                align-items: baseline;
                gap: 8px;
                color: {color};
            ">
                <span style="font-size: 1.8em; font-weight: 600;">
                    {fmt_eur(total_pl)}
                </span>
                <span style="font-size: 0.7em;">
                    EUR
                </span>
                <span style="font-size: 1em; color: {pct_color};">
                    {fmt_pct(total_pct)}
                </span>
            </div>
            <div style="
                margin-top: 10px;
                font-size: 0.85em;
                color: #9aa0a6;
                display: flex;
                justify-content: space-between;
            ">
                <span>Rendimento annualizzato</span>
                <span>
                    {fmt_pct(annualized_pct) if annualized_pct is not None else ""}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
