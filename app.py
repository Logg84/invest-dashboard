import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Strategic Investment Terminal", layout="wide")
st.title("🌍 Strategic Investment Terminal")
st.markdown("Analisi Automatica Multi-Asset basata su Momentum e Forza Relativa")

# --- DATABASE DEGLI ASSET DA ANALIZZARE ---
assets_db = {
    "GEO": [
        {"ticker": "SPY", "name": "USA (S&P 500)", "type": "Indice/ETF"},
        {"ticker": "FEZ", "name": "Europa (Euro Stoxx 50)", "type": "Indice/ETF"},
        {"ticker": "EEM", "name": "Emerging Markets", "type": "Indice/ETF"},
        {"ticker": "INDA", "name": "India", "type": "ETF Paese"},
        {"ticker": "FXI",  "name": "Cina Large Cap", "type": "ETF Paese"},
        {"ticker": "EWJ",  "name": "Giappone", "type": "ETF Paese"},
    ],
    "SECTOR": [
        {"ticker": "XLK", "name": "Technology", "type": "Settoriale"},
        {"ticker": "XLE", "name": "Energy", "type": "Settoriale"},
        {"ticker": "XLF", "name": "Financials", "type": "Settoriale"},
        {"ticker": "XLI", "name": "Industrials", "type": "Settoriale"},
        {"ticker": "XLV", "name": "Healthcare", "type": "Settoriale"},
        {"ticker": "ITA", "name": "Aerospace & Defense", "type": "Settoriale Spec."},
        {"ticker": "GDX", "name": "Gold Miners", "type": "Settoriale Spec."},
    ],
    "PILLARS": [
        {"ticker": "GLD", "name": "Oro (Difesa)", "pillar": "1. Airbag"},
        {"ticker": "COPX", "name": "Rame (Infra)", "pillar": "2. Real AI"},
        {"ticker": "URA", "name": "Uranio", "pillar": "2. Real AI"},
        {"ticker": "IWM", "name": "Small Caps", "pillar": "3. Ciclici"},
        {"ticker": "BTC-USD", "name": "Bitcoin", "pillar": "4. Speculativi"},
    ]
}

# --- MOTORE DI ANALISI DATI ---
@st.cache_data(ttl=3600)
def analyze_market(ticker_list, category_label):
    results = []
    for item in ticker_list:
        ticker = item['ticker']
        # Scarica dati ultimi 6 mesi
        df = yf.download(ticker, period="6mo", progress=False)
        
        if len(df) > 0:
            current_price = float(df['Close'].iloc[-1])
            start_price_3m = float(df['Close'].iloc[-65]) if len(df) > 65 else float(df['Close'].iloc[0])
            start_price_1m = float(df['Close'].iloc[-22]) if len(df) > 22 else float(df['Close'].iloc[0])
            
            perf_3m = ((current_price - start_price_3m) / start_price_3m) * 100
            perf_1m = ((current_price - start_price_1m) / start_price_1m) * 100
            
            # Volatilità
            daily_returns = df['Close'].pct_change()
            volatility = float(daily_returns.std() * np.sqrt(252) * 100)
            
            # Score
            score = (perf_3m * 0.7) + (perf_1m * 0.3)
            
            # Suggerimento
            suggestion = "Hold/Wait"
            if score > 5:
                if volatility > 25:
                    suggestion = "ETF (Per diluire rischio)"
                else:
                    suggestion = "Azioni Singole / Future"
            elif score < -5:
                suggestion = "Evitare / Short"
            else:
                suggestion = "Accumulo PAC"

            results.append({
                "Nome": item['name'],
                "Ticker": ticker,
                "Prezzo": round(current_price, 2),
                "Perf 1M %": round(perf_1m, 2),
                "Perf 3M %": round(perf_3m, 2),
                "Score (Forza)": round(score, 2),
                "Suggerimento": suggestion
            })
            
    return pd.DataFrame(results).sort_values(by="Score (Forza)", ascending=False)

# --- VISUALIZZAZIONE ---
st.subheader("1. 🗺️ Analisi Geografica")
df_geo = analyze_market(assets_db['GEO'], "Geografia")
st.dataframe(df_geo.style.background_gradient(subset=['Score (Forza)'], cmap='RdYlGn'), use_container_width=True)

st.markdown("---")

st.subheader("2. 🏭 Analisi Settoriale")
df_sector = analyze_market(assets_db['SECTOR'], "Settori")
st.dataframe(df_sector.style.background_gradient(subset=['Score (Forza)'], cmap='RdYlGn'), use_container_width=True)

st.markdown("---")

st.subheader("3. 🏛️ I 4 Pilastri")
df_pillars = analyze_market(assets_db['PILLARS'], "Pilastri")
col1, col2, col3, col4, col5 = st.columns(5)
metrics = df_pillars.to_dict('records')

# Mostra metriche rapide
if len(metrics) >= 5:
    col1.metric(metrics[0]['Nome'], f"{metrics[0]['Prezzo']}", f"{metrics[0]['Perf 1M %']}%")
    col2.metric(metrics[1]['Nome'], f"{metrics[1]['Prezzo']}", f"{metrics[1]['Perf 1M %']}%")
    col3.metric(metrics[2]['Nome'], f"{metrics[2]['Prezzo']}", f"{metrics[2]['Perf 1M %']}%")
    col4.metric(metrics[3]['Nome'], f"{metrics[3]['Prezzo']}", f"{metrics[3]['Perf 1M %']}%")
    col5.metric(metrics[4]['Nome'], f"{metrics[4]['Prezzo']}", f"{metrics[4]['Perf 1M %']}%")

st.dataframe(df_pillars)
st.caption(f"Ultimo aggiornamento: {pd.Timestamp.now()}")
