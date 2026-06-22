import streamlit as st

from services.market_data import download_intraday_range
from services.market_status import compute_data_quality_label


def render_market_data_status(
    closes,
    filtered_tickers,
    ops_filtered,
    tz_name="Europe/Rome"
):
    intraday_range = download_intraday_range(filtered_tickers)

    markets = []
    if "Mercato" in ops_filtered.columns:
        markets = (
            ops_filtered["Mercato"]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )

    label, _ = compute_data_quality_label(
        closes=closes,
        intraday_range=intraday_range,
        markets=markets,
        tz_name=tz_name
    )

    st.caption(label)
