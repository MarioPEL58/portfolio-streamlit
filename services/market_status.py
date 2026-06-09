from datetime import datetime
import pandas as pd
import pytz


def _to_local_tz(ts, tz):
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


def compute_market_update_label(closes, intraday_last_ts=None, tz_name="Europe/Rome"):
    tz = pytz.timezone(tz_name)
    now = datetime.now(tz)

    # =========================
    # 1. se ho timestamp intraday → uso quello
    # =========================
    if intraday_last_ts is not None:
        ts_local = _to_local_tz(intraday_last_ts, tz)

        if ts_local is not None:
            delay_minutes = int((now - ts_local).total_seconds() / 60)
            delay_minutes = max(delay_minutes, 0)

            last_update = now.strftime("%H:%M:%S %Z")

            if delay_minutes < 5:
                status = "✅ quasi realtime"
            elif delay_minutes < 30:
                status = f"⏱️ ritardo ~{delay_minutes} min"
            elif delay_minutes < 300:
                status = f"⚠️ ritardo ~{delay_minutes} min"
            else:
                status = "🕒 mercato chiuso"

            return f"Ultimo aggiornamento: {last_update} • {status}"

    # =========================
    # 2. fallback daily
    # =========================
    if closes is None or closes.empty:
        return "⚠️ Nessun dato prezzi disponibile"

    last_date = pd.Timestamp(closes.index.max()).date()
    today = now.date()
    days_diff = (today - last_date).days

    last_update = now.strftime("%H:%M:%S %Z")

    if days_diff == 0:
        status = "⏱️ dati aggiornati (delay intraday)"
    elif days_diff == 1:
        status = "🕒 mercato chiuso (ultimo giorno utile)"
    else:
        status = f"⚠️ dati vecchi ({days_diff} giorni)"

    return f"Ultimo aggiornamento: {last_update} • {status}"
