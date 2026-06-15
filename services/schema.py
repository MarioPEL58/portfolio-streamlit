COLUMN_ALIASES = {
    "ID": ["id"],
    "Intermediario": ["intermediario", "broker", "banca", "conto", "account"],
    "Ticker": ["ticker", "symbol", "simbolo", "isin"],
    "Data": ["data", "date"],
    "Quantita": ["quantità", "quantita", "quantity", "qty", "qta"],
    "Prezzo": ["prezzo", "price"],
    "SpeseEuro": ["spese euro", "spese", "commissioni", "fees", "fee"],
    "Tassa": ["tassa", "tax"],
    "Cambio": ["cambio", "fx", "exchange rate"],
    "FlussoNetto": ["flusso netto", "cash flow", "net cash flow"],
    "Prezzo medio s/carico": ["prezzo medio", "pmc", "average price"],
    "Nome": ["nome", "name", "descrizione"],
    "Tipo": ["tipo", "type", "categoria"],
    "Area": ["area", "region", "geografia"],
    "Settore": ["settore", "sector", "industry"],
    "Emittente": ["emittente", "issuer", "provider"],
    "Valuta": ["valuta", "currency"],
}
DIVIDEND_ALIASES = {
    "ID": ["id"],
    "Data": ["data", "date"],
    "DividendoNetto": [
        "dividendi euro netti",
        "dividendo netto",
        "net dividend"
    ],
    "DividendoTotale": [
        "dividendi totali euro",
        "dividendo totale",
        "gross dividend"
    ],
    "Nome": ["nome", "name"],
    "Valuta": ["valuta", "currency"]
}
REQUIRED_COLUMNS = ["Ticker", "Data", "Quantita"]
DIVIDEND_REQUIRED_COLUMNS = ["Data", "DividendoNetto"]
SHEET_ALIASES = {
    "Operazioni": [
        "operazioni",
        "operations",
        "trades",
        "movimenti",
        "transactions",
        "orders"
    ],

    "DividendiCedole": [
        "dividendi cedole",
        "dividendi",
        "cedole",
        "dividends",
        "coupons",
        "income"
    ]
}
def find_sheet_name(sheet_names, aliases):
    normalized_sheets = {
        normalize_text(s): s for s in sheet_names
    }

    for alias in aliases:
        key = normalize_text(alias)
        if key in normalized_sheets:
            return normalized_sheets[key]

    # fallback: match parziale
    for sheet in sheet_names:
        n_sheet = normalize_text(sheet)
        if any(normalize_text(alias) in n_sheet for alias in aliases):
            return sheet

    return None
