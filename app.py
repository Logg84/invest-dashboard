import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Strategic Terminal v14.0 (Light)", layout="wide")
st.markdown("""
<style>
    .stButton>button { width: 100%; padding: 0px; font-size: 0.8rem; height: 2em;}
    div[data-testid="stVerticalBlock"] > div { gap: 0.1rem; }
    .metric-container { background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- DATABASE SEMPLIFICATO (Solo i Proxy) ---
db = {
    "GEO": [
        ("USA (S&P 500)", "SPY"), ("India", "INDA"), ("Cina", "FXI"), 
        ("Europa", "IEUR"), ("Giappone", "EWJ"), ("Germania", "EWG"),
        ("Regno Unito", "EWU"), ("Italia", "EWI"), ("Brasile", "EWZ"),
        ("Taiwan", "EWT"), ("Corea Sud", "EWY"), ("Messico", "EWW")
    ],
    "SECTOR": [
        ("Technology", "XLK"), ("Semiconductors", "SMH"), ("Energy", "XLE"),
        ("Healthcare", "XLV"), ("Financials", "XLF"), ("Defense", "ITA"),
        ("Gold Miners", "GDX"), ("Uranium", "URA"), ("Cybersecurity", "CIBR"),
        ("Robotics & AI", "BOTZ"), ("Biotech", "IBB"), ("Staples", "XLP")
    ],
    "PILLARS": [
        ("1. ORO (Difesa)", "GLD"), ("2. RAME (Infra)", "COPX"),
        ("3. SMALL CAP (Ciclo)", "IWM"), ("4. BITCOIN (Risk)", "BTC-USD")
    ]
}

# --- FUNZIONE ANALISI SINGOLA (Anti-Crash) ---
def analyze_single_asset(name, ticker):
    """Scarica, Analizza e Restituisce i dati per una singola riga"""
    try:
        # Scarica solo ultimi 6 mesi per velocità massima
        df = yf.download(ticker, period="6mo", progress=False)
        
        if df.empty or len(df) < 5:
            return None # Dato mancante
            
        # Fix per Serie/DataFrame
        closes = df['Close']
        if isinstance(closes, pd.DataFrame): closes = closes.iloc[:, 0]
        
        curr = float(closes.iloc[-1])
        
        # Prezzi storici
        def get_px(days):
            idx = -days if len(closes) > days else 0
            return float(closes.iloc[idx])
            
        p1m = get_px(22)
        p3m = get_px(65)
        
        perf_1m = ((curr - p1m)/p1m)*100
        perf_3m = ((curr - p3m)/p3m)*100
        
        # Score Semplificato
        score = (perf_3m * 0.6) + (perf_1m * 0.4)
        score = max(min(score/2.0, 10), -10) # Divisore 2.0
        
        return {
            "name": name,
            "ticker": ticker,
            "score": score,
            "p1m": perf_1m,
            "p3m": perf_3m,
            "price": curr
        }
    except Exception:
        return None

# --- UI COMPONENT ---
def render_row(stats):
    if not stats: return
    
    c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
    
    # Col 1: Nome + Icona
    icon = "🔥" if stats['score'] > 6 else ("❄️" if stats['score'] < -6 else "➖")
    c1.markdown(f"**{icon} {stats['name']}**")
    
    # Col 2: Score
    color = "green" if stats['score'] > 0 else "red"
    c2.markdown(f":{color}[**{stats['score']:.1f}**]")
    
    # Col 3 & 4: Performance
    c3.markdown(f"{stats['p1m']:.1f}% (1M)")
    c4.markdown(f"{stats['p3m']:.1f}% (3M)")
    
    # Col 5: Link Esterno
    url = f"https://finance.yahoo.com/quote/{stats['ticker']}"
    c5.link_button("Grafico 🌐", url)

def render_section(title, data_list):
    st.subheader(title)
    
    # Intestazione
    h1, h2, h3, h4, h5 = st.columns([3, 1, 1, 1, 1])
    h1.caption("ASSET")
    h2.caption("SCORE")
    h3.caption("1 MESE")
    h4.caption("3 MESI")
    h5.caption("DETTAGLI")
    st.divider()
    
    # Caricamento Live (Uno alla volta per non bloccare)
    results = []
    placeholder = st.empty()
    
    # Barra di progresso locale per sezione
    prog_bar = st.progress(0)
    
    for i, (name, ticker) in enumerate(data_list):
        stats = analyze_single_asset(name, ticker)
        if stats:
            results.append(stats)
        prog_bar.progress((i+1)/len(data_list))
        # time.sleep(0.05) # Micro pausa tecnica
        
    prog_bar.empty()
    
    # Ordina i risultati per Score decrescente
    results.sort(key=lambda x: x['score'], reverse=True)
    
    if not results:
        st.error("Dati non disponibili per questa sezione.")
    else:
        for r in results:
            render_row(r)
            st.markdown("<hr style='margin: 0.2em 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

# --- MAIN APP ---
st.title("🌍 Strategic Terminal v14.0 (Light)")

# Bottone Ricarica Manuale
if st.button("🔄 AGGIORNA DATI ORA"):
    st.cache_data.clear()
    st.rerun()

col_L, col_R = st.columns(2)

with col_L:
    render_section("1. 🗺️ CLASSIFICA NAZIONI", db['GEO'])

with col_R:
    render_section("2. 🏭 CLASSIFICA SETTORI", db['SECTOR'])

st.markdown("---")
render_section("3. 🏛️ I 4 PILASTRI", db['PILLARS'])
