import io
import pandas as pd


def create_demo_file():

    # -------------------------
    # Foglio Readme con informazioni
    # -------------------------
  
    df_readme = pd.DataFrame({
         "Istruzioni": [
             "Compila il foglio Operazioni con i tuoi dati.",
             "Inserisci quantità positive per acquisti e negative per vendite.",
             "Il foglio DividendiCedole è facoltativo.",
             "Non modificare i nomi delle colonne."
         ]
     })

  
    # -------------------------
    # Foglio Operazioni (INPUT PURO)
    # -------------------------
    df_ops = pd.DataFrame([
        {
            "ID": 9,
            "Statistiche": "1",
            "Nome": "A2A",
            "Tipo": "AZ",
            "Classe": "Azioni",
            "Area": "IT",
            "Settore": "Energia",
            "Emittente": "A2A",
            "Valuta": "EUR",
            "ISIN": "IT0001233417",
            "Ticker": "A2A.MI",
            "Tassa": 0.26,
            "Data": "2026-03-24",
            "Mercato": "MTA",
            "Intermediario": "CreditAgricole",
            "Quantità": 1000,
            "Prezzo": 2.31427,
            "Spese valuta": 1.00,
            "Cambio": 1.0,
            "Spese euro": 1.00,
        },
        {
            "ID": 10,
            "Statistiche": "1",
            "Nome": "BANCA Monte dei Paschi di Siena",
            "Tipo": "AZ",
            "Classe": "Azioni",
            "Area": "IT",
            "Settore": "Finanza",
            "Emittente": "BMPS",
            "Valuta": "EUR",
            "ISIN": "IT0005218752",
            "Ticker": "BMPS.MI",
            "Tassa": 0.26,
            "Data": "2026-03-25",
            "Mercato": "MTA",
            "Intermediario": "CreditAgricole",
            "Quantità": 400,
            "Prezzo": 7.5080,
            "Spese valuta": 5.56,
            "Cambio": 1.0,
            "Spese euro": 5.56,
        },
        {
            "ID": 11,
            "Statistiche": "1",
            "Nome": "Webuild SpA",
            "Tipo": "AZ",
            "Classe": "Azioni",
            "Area": "IT",
            "Settore": "Industriali",
            "Emittente": "Webuild",
            "Valuta": "EUR",
            "ISIN": "IT0003865570",
            "Ticker": "WBD.MI",
            "Tassa": 0.26,
            "Data": "2026-03-24",
            "Mercato": "MTA",
            "Intermediario": "CreditAgricole",
            "Quantità": 1500,
            "Prezzo": 2.31430,
            "Spese valuta": 6.41,
            "Cambio": 1.0,
            "Spese euro": 6.41,
        },
        {
            "ID": 12,
            "Statistiche": "1",
            "Nome": "Replay",
            "Tipo": "AZ",
            "Classe": "Azioni",
            "Area": "IT",
            "Settore": "Consumer",
            "Emittente": "Replay",
            "Valuta": "EUR",
            "ISIN": "IT0004965148",
            "Ticker": "REY.MI",
            "Tassa": 0.26,
            "Data": "2026-03-12",
            "Mercato": "MTA",
            "Intermediario": "CreditAgricole",
            "Quantità": 40,
            "Prezzo": 93.85,
            "Spese valuta": 6.94,
            "Cambio": 1.0,
            "Spese euro": 6.94,
        },
        {
            "ID": 13,
            "Statistiche": "1",
            "Nome": "Sandisk",
            "Tipo": "AZ",
            "Classe": "Azioni",
            "Area": "USA",
            "Settore": "Tech",
            "Emittente": "Sandisk",
            "Valuta": "USD",
            "ISIN": "US80105N1054",
            "Ticker": "SNDK",
            "Tassa": 0.26,
            "Data": "2026-03-23",
            "Mercato": "NASDAQ",
            "Intermediario": "IBK",
            "Quantità": 3,
            "Prezzo": 692.85,
            "Spese valuta": 0.30,
            "Cambio": 0.86236633,
            "Spese euro": 0.00,
        },
        {
            "ID": 13,
            "Statistiche": "1",
            "Nome": "Sandisk",
            "Tipo": "AZ",
            "Classe": "Azioni",
            "Area": "USA",
            "Settore": "Tech",
            "Emittente": "Sandisk",
            "Valuta": "USD",
            "ISIN": "US80105N1054",
            "Ticker": "SNDK",
            "Tassa": 0.26,
            "Data": "2026-04-08",
            "Mercato": "NASDAQ",
            "Intermediario": "IBK",
            "Quantità": -3,
            "Prezzo": 792.90,
            "Spese valuta": 0.00,
            "Cambio": 0.854262,
            "Spese euro": 0.00,
        },
        {
            "ID": 14,
            "Statistiche": "1",
            "Nome": "ALBEMARLE CORP",
            "Tipo": "AZ",
            "Classe": "Azioni",
            "Area": "USA",
            "Settore": "Energy Storage",
            "Emittente": "Albemarle",
            "Valuta": "USD",
            "ISIN": "US0126531013",
            "Ticker": "ALB",
            "Tassa": 0.26,
            "Data": "2026-04-16",
            "Mercato": "NYSE",
            "Intermediario": "IBK",
            "Quantità": 10,
            "Prezzo": 170.33,
            "Spese valuta": 0.28,
            "Cambio": 0.854262,
            "Spese euro": 0.00,
        },
        {
            "ID": 14,
            "Statistiche": "1",
            "Nome": "ALBEMARLE CORP",
            "Tipo": "AZ",
            "Classe": "Azioni",
            "Area": "USA",
            "Settore": "Energy Storage",
            "Emittente": "Albemarle",
            "Valuta": "USD",
            "ISIN": "US0126531013",
            "Ticker": "ALB",
            "Tassa": 0.26,
            "Data": "2026-04-16",
            "Mercato": "NYSE",
            "Intermediario": "IBK",
            "Quantità": -10,
            "Prezzo": 215.00,
            "Spese valuta": 0.37,
            "Cambio": 0.848824,
            "Spese euro": 0.00,
        },
        {
            "ID": 23,
            "Statistiche": "1",
            "Nome": "MP Materials Corp",
            "Tipo": "AZ",
            "Classe": "Azioni",
            "Area": "USA",
            "Settore": "Materiali",
            "Emittente": "MP",
            "Valuta": "USD",
            "ISIN": "US5533681012",
            "Ticker": "MP",
            "Tassa": 0.26,
            "Data": "2026-05-22",
            "Mercato": "NYSE",
            "Intermediario": "IBK",
            "Quantità": 20,
            "Prezzo": 63.62,
            "Spese valuta": 0.00,
            "Cambio": 0.86,
            "Spese euro": 0.00,
        },
        {
            "ID": 23,
            "Statistiche": "1",
            "Nome": "MP Materials Corp",
            "Tipo": "AZ",
            "Classe": "Azioni",
            "Area": "USA",
            "Settore": "Materiali",
            "Emittente": "MP",
            "Valuta": "USD",
            "ISIN": "US5533681012",
            "Ticker": "MP",
            "Tassa": 0.26,
            "Data": "2026-05-22",
            "Mercato": "NYSE",
            "Intermediario": "IBK",
            "Quantità": -20,
            "Prezzo": 63.00,
            "Spese valuta": 0.00,
            "Cambio": 0.86,
            "Spese euro": 0.00,
        },
    ])
    # -------------------------
    # Foglio DividendiCedole
    # -------------------------
    df_div = pd.DataFrame([
        {
            "ID": 9,
            "Data": "2026-05-20",
            "Dividendi euro Netti": 76.96,
            "Nome": "A2A",
            "Valuta": "EUR"
        },
        {
            "ID": 11,
            "Data": "2026-05-20",
            "Dividendi euro Netti": 89.91,
            "Nome": "Webuild SpA",
            "Valuta": "EUR"
        }
    ])

    # -------------------------
    # File Excel
    # -------------------------
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_readme.to_excel(writer, sheet_name="README", index=False)
        df_ops.to_excel(writer, sheet_name="Operazioni", index=False)
        df_div.to_excel(writer, sheet_name="DividendiCedole", index=False)

    buffer.seek(0)
    return buffer
