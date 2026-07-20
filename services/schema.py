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
REQUIRED_OPERATION_COLUMNS = ["Ticker", "Data", "Quantita"]
REQUIRED_DIVIDEND_COLUMNS = ["Data", "DividendoNetto"]
REQUIRED_START_COLUMNS = ["Data", "Ticker", "Quantita", "Prezzo"]
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
    ],
    # ✅ NUOVO
    "Start": [
        "start",
        "iniziale",
        "posizioni iniziali",
        "portafoglio iniziale",
        "baseline",
        "opening"
    ]
}
