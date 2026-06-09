from datetime import datetime
import pytz


def compute_market_update_label(closes):
    if closes is None or closes.empty:
        return "⚠️ Nessun dato prezzi disponibile"

    tz = pytz.timezone("Europe/Rome")
    now = datetime.now(tz)

    last_price_time = closes.index.max()

    # gestione timezone safe
    try:
        last_price_time = last_price_time.tz_localize("UTC").tz_convert(tz)
    except:
        try:
            last_price_time = last_price_time.tz_convert(tz)
        except:
            last_price_time = last_price_time  # fallback

    delay_minutes = (now - last_price_time).total_seconds() / 60

    last_update = now.strftime("%H:%M:%S %Z")

    # stato
    if delay_minutes < 5:
        status = "✅ realtime"
    elif delay_minutes < 30:
        status = f"⏱️ {int(delay_minutes)} min"
    elif delay_minutes < 300:
        status = f"⚠️ {int(delay_minutes)} min"
    else:
        status = "🕒 mercato chiuso"

    return f"Ultimo aggiornamento: {last_update} • {status}"
