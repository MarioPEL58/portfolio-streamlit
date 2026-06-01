# Portfolio Tracker ETF / Azioni — Streamlit App

Applicazione Streamlit per ricostruire il valore del portafoglio nel tempo a partire da un file Excel di operazioni.

## Funzionalità
- Upload di file Excel
- Lettura del foglio `Operazioni` (oppure foglio compatibile)
- Parsing delle colonne:
  - `Ticker`
  - `Data`
  - `Quantità`
  - `Prezzo`
  - `Spese euro`
- Download dei prezzi storici giornalieri da Yahoo Finance
- Calcolo di:
  - Valore portafoglio nel tempo
  - Capitale investito
  - P/L totale
  - Posizioni correnti
  - Allocazione per ticker / area / tipo
- Download CSV dei risultati

## Avvio in locale

```bash
pip install -r requirements.txt
streamlit run app.py
