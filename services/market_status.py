import streamlit as st
from datetime import datetime, time
import pandas as pd
import pytz
from utils.i18n import t
from services.market_data import download_intraday_range

MARKET_HOURS = {
    "MILANO": {"open": (9, 0), "close": (17, 30)},
    "USA": {"open": (15, 30), "close": (22, 0)},
    "XETRA": {"open": (9, 0), "close": (17, 30)},
}


def normalize_market(market):
    if market is None:
        return None
    value = str(market).strip().upper()
    return value if value else None


def to_local_timestamp(ts, tz):
    if ts is None:
        return None

    ts = pd.Timestamp(ts)

    try:
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        ts = ts.tz_convert(tz)
    except Exception:
        try:
            ts = ts.tz_localize(tz)
        except Exception:
            pass

    return ts


def is_market_open(now_local, market_name):
    market_name = normalize_market(market_name)

    if market_name not in MARKET_HOURS:
        market_name = "MILANO"

    open_h, open_m = MARKET_HOURS[market_name]["open"]
    close_h, close_m = MARKET_HOURS[market_name]["close"]

    market_open = time(open_h, open_m)
    market_close = time(close_h, close_m)

    return market_open <= now_local.time() <= market_close


def compute_market_update_label(closes, intraday_last_ts=None, markets=None, tz_name="Europe/Rome"):
    tz = pytz.timezone(tz_name)
    now = datetime.now(tz)
    last_update = now.strftime("%H:%M:%S %Z")

    # weekend
    if now.weekday() >= 5:
        return f"{t('last_update_label')}: {last_update} • 🕒 {t('market_closed')} ({t('weekend')})"

    # normalizzazione mercati
    normalized_markets = []
    if markets:
        normalized_markets = [
            normalize_market(m) for m in markets
            if normalize_market(m) is not None
        ]

    # fallback su Milano se campo Mercato mancante/vuoto
    if not normalized_markets:
        normalized_markets = ["MILANO"]

    # se almeno un mercato è aperto → gestisco delay
    any_market_open = any(is_market_open(now, m) for m in normalized_markets)

    if not any_market_open:
        if len(set(normalized_markets)) == 1:
            return (
                f"{t('last_update_label')}: {last_update} • "
                f"🕒 {t('market_closed')} ({normalized_markets[0].title()})"
            )
        return f"{t('last_update_label')}: {last_update} • 🕒 {t('markets_closed')}"

    # se ho timestamp intraday reale → uso quello
    if intraday_last_ts is not None:
        ts_local = to_local_timestamp(intraday_last_ts, tz)

        if ts_local is not None:
            delay_minutes = int((now - ts_local).total_seconds() / 60)
            delay_minutes = max(delay_minutes, 0)

            if delay_minutes < 5:
                status = f"✅ {t('almost_realtime')}"
            elif delay_minutes < 30:
                status = f"⏱️ {t('delay')} ~{delay_minutes} {t('minutes')}"
            else:
                status = f"⚠️ {t('delay')} ~{delay_minutes} {t('minutes')}"

            return f"{t('last_update_label')}: {last_update} • {status}"

    # fallback su dati daily
    if closes is None or closes.empty:
        return f"{t('last_update_label')}: {last_update} • ⚠️ {t('no_price_data')}"

    last_date = pd.Timestamp(closes.index.max()).date()
    today = now.date()
    days_diff = (today - last_date).days

    if days_diff == 0:
        status = f"⏱️ {t('intraday_delay_data')}"
    elif days_diff == 1:
        status = f"🕒 {t('last_useful_day')}"
    else:
        status = f"⚠️ {t('old_data')} ({days_diff} {t('days')})"

    return f"{t('last_update_label')}: {last_update} • {status}"

def compute_data_quality_label(
    closes: pd.DataFrame,
    intraday_range,
    markets=None,
    tz_name="Europe/Rome"
):
    tz = pytz.timezone(tz_name)
    now = datetime.now(tz)

    # ===== storico =====
    price_min = None
    price_max = None

    if closes is not None and not closes.empty:
        valid = closes.dropna(how="all")
        if not valid.empty:
            price_min = valid.index.min()
            price_max = valid.index.max()

    # ===== intraday =====
    intraday_min, intraday_max = intraday_range if intraday_range else (None, None)

    # ===== label =====
    parts = []

    if intraday_max is not None:
        parts.append(f"Ultimo aggiornamento: {intraday_max:%H:%M:%S}")
    elif price_max is not None:
        parts.append(f"Ultimo prezzo: {price_max:%d/%m/%Y}")

    # stato mercato
    if intraday_max is not None and intraday_max.date() == now.date():
        parts.append("🟢 LIVE")
    else:
        parts.append("🕒 mercato chiuso")

    # storico
    if price_min and price_max:
        parts.append(f"📅 {price_min:%d/%m/%Y} → {price_max:%d/%m/%Y}")

    # intraday
    if intraday_min and intraday_max:
        parts.append(f"📡 {intraday_min:%H:%M} → {intraday_max:%H:%M}")

    label = " • ".join(parts)

    return label, {
        "price_min": price_min,
        "price_max": price_max,
        "intraday_min": intraday_min,
        "intraday_max": intraday_max,
    }


def render_market_data_status(
    closes,
    filtered_tickers,
    ops_filtered,
    tz_name="Europe/Rome"
):
    # intraday
    intraday_range = download_intraday_range(filtered_tickers)

    # mercati
    markets = []
    if "Mercato" in ops_filtered.columns:
        markets = (
            ops_filtered["Mercato"]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )

    # label
    label, meta = compute_data_quality_label(
        closes=closes,
        intraday_range=intraday_range,
        markets=markets,
        tz_name=tz_name
    )

    st.caption(label)

    return meta
