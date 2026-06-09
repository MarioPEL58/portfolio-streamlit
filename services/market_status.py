from datetime import datetime, time
import pandas as pd
import pytz


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
        return f"Ultimo aggiornamento: {last_update} • 🕒 mercato chiuso (weekend)"

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
            return f"Ultimo aggiornamento: {last_update} • 🕒 mercato chiuso ({normalized_markets[0].title()})"
        return f"Ultimo aggiornamento: {last_update} • 🕒 mercati chiusi"

    # se ho timestamp intraday reale → uso quello
    if intraday_last_ts is not None:
        ts_local = to_local_timestamp(intraday_last_ts, tz)

        if ts_local is not None:
            delay_minutes = int((now - ts_local).total_seconds() / 60)
            delay_minutes = max(delay_minutes, 0)

            if delay_minutes < 5:
                status = "✅ quasi realtime"
            elif delay_minutes < 30:
                status = f"⏱️ ritardo ~{delay_minutes} min"
            else:
                status = f"⚠️ ritardo ~{delay_minutes} min"

            return f"Ultimo aggiornamento: {last_update} • {status}"

    # fallback su dati daily
    if closes is None or closes.empty:
        return f"Ultimo aggiornamento: {last_update} • ⚠️ nessun dato prezzi"

    last_date = pd.Timestamp(closes.index.max()).date()
    today = now.date()
    days_diff = (today - last_date).days

    if days_diff == 0:
        status = "⏱️ dati aggiornati (delay intraday)"
    elif days_diff == 1:
        status = "🕒 ultimo giorno utile"
    else:
        status = f"⚠️ dati vecchi ({days_diff} giorni)"

    return f"Ultimo aggiornamento: {last_update} • {status}"
