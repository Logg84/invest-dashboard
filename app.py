import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import calendar
import time

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Strategic Terminal v13.0", layout="wide")
st.markdown("""
<style>
    .stButton>button { width: 100%; height: 1.8em; padding: 0px; font-size: 0.8rem; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.2rem; }
    .score-val { font-weight: bold; font-size: 1.1em; }
</style>
""", unsafe_allow_html=True)

# --- DATABASE ---
db = {
    "GEO": {
        "USA (S&P 500)": { "p": "SPY", "assets": ["VOO", "QQQ", "IWM", "MSFT", "NVDA"]},
        "India": { "p": "INDA", "assets": ["INDA", "EPI", "SMIN", "INFY", "HDB"]},
        "Cina": { "p": "FXI", "assets": ["FXI", "KWEB", "MCHI", "BABA", "PDD"]},
        "Europa": { "p": "IEUR", "assets": ["VGK", "EZU", "FEZ", "NVO", "ASML"]},
        "Giappone": { "p": "EWJ", "assets": ["EWJ", "DXJ", "SONY", "TM", "HMC"]},
        "Germania": { "p": "EWG", "assets": ["EWG", "DAX", "SAP", "SIEGY", "DTEGY"]},
        "Regno Unito": { "p": "EWU", "assets": ["EWU", "FLGB", "SHEL", "HSBC", "BP"]},
        "Italia": { "p": "EWI", "assets": ["EWI", "RACE", "STLA", "E", "IIALY"]},
        "Brasile": { "p": "EWZ", "assets": ["EWZ", "PBR", "VALE", "NU", "ITUB"]},
        "Taiwan": { "p": "EWT", "assets": ["EWT", "TSM", "UMC", "ASX", "IMOS"]},
        "Corea del Sud": { "p": "EWY", "assets": ["EWY", "PKX", "KB", "LPL", "SKM"]},
        "Messico": { "p": "EWW", "assets": ["EWW", "AMX", "FMX", "VLRS", "CX"]},
    },
    "SECTOR": {
        "Technology": { "p": "XLK", "assets": ["XLK", "VGT", "MSFT", "AAPL", "ADBE"]},
        "Semiconductors": { "p": "SMH", "assets": ["SMH", "SOXX", "NVDA", "AVGO", "AMD"]},
        "Energy": { "p": "XLE", "assets": ["XLE", "XOM", "CVX", "COP", "EOG"]},
        "Healthcare": { "p": "XLV", "assets": ["XLV", "LLY", "UNH", "JNJ", "ABBV"]},
        "Financials": { "p": "XLF", "assets": ["XLF", "JPM", "BAC", "WFC", "GS"]},
        "Defense": { "p": "ITA", "assets": ["ITA", "XAR", "RTX", "LMT", "GD"]},
        "Gold Miners": { "p": "GDX", "assets": ["GDX", "NEM", "GOLD", "AEM", "KGC"]},
        "Uranium": { "p": "URA", "assets": ["URA", "URNM", "CCJ", "UEC", "NXE"]},
        "Cybersecurity": { "p": "CIBR", "assets": ["CIBR", "HACK", "PANW", "CRWD", "FTNT"]},
        "Robotics & AI": { "p": "BOTZ", "assets": ["BOTZ", "ROBO", "PATH", "ISRG", "TER"]},
        "Biotech": { "p": "IBB", "assets": ["IBB", "XBI", "VRTX", "REGN", "AMGN"]},
        "Cons. Staples": { "p": "XLP", "assets": ["XLP", "PG", "COST", "PEP", "KO"]},
    },
    "PILLARS": {
        "1. DIFESA": { "p": "GLD", "assets": ["IAU", "SHY", "SLV"] },
        "2. INFRA / AI": { "p": "COPX", "assets": ["URA", "PAVE", "GRID"] },
        "3. CICLICI": { "p": "IWM", "assets": ["VTV", "IJR", "EEM"] },
        "4. SPECULATIVI": { "p": "BTC-USD", "assets": ["ETH-USD", "IBIT", "TQQQ"] }
    }
}

# --- ENGINE: BATCH DOWNLOAD (IL SEGRETO PER LA VELOCITÀ) ---
@st.cache_data(ttl=3600)
def load_all_proxies(ticker_list):
    """Scarica TUTTI i proxy in una sola chiamata API"""
    try:
        data = yf.download(ticker_list, period="2y", group_by='ticker', progress=False, threads=True)
        return data
    except:
        return None

def calculate_stats(df):
    """Calcola Score, Trend e Stagionalità da un DataFrame singolo"""
    if df is None or len(df) < 20: return None
    
    # Fix per Serie vs DataFrame
    try:
        closes = df['Close']
        if isinstance(closes, pd.DataFrame):
            closes = closes.iloc[:, 0] # Prendi la prima colonna se è doppio livello
            
        curr = float(closes.iloc[-1])
        
        def get_px(d): 
            idx = -d if len(closes) > d else 0
            return float(closes.iloc[idx])

        p1m, p3m, p6m, p1y = get_px(22), get_px(65), get_px(130), get_px(252)
        
        perf_1m = ((curr - p1m)/p1m)*100
        perf_3m = ((curr - p3m)/p3m)*100
        perf_6m = ((curr - p6m)/p6m)*100
        perf_1y = ((curr - p1y)/p1y)*100
        
        # Algoritmo Severo (/3.0)
        w_perf = (perf_3m*0.4) + (perf_1m*0.3) + (perf_6m*0.2) + (perf_1y*0.1)
        score = max(min(w_perf / 3.0, 10), -10)
        
        # Score storici (approssimati)
        score_1m = score - (perf_1m / 10) # Stima trend score
        
        # Stagionalità
        df_temp = pd.DataFrame(closes)
        df_temp['M'] = df_temp.index.month
        monthly = df_temp.groupby('M').mean() # Semplificato per velocità
        best_month = calendar.month_abbr[monthly.idxmax().iloc[0]]

        return {
            "price": curr,
            "score": score,
            "score_prev": score_1m,
            "p1m": perf_1m, "p3m": perf_3m, "p6m": perf_6m, "p1y": perf_1y,
            "best_month": best_month
        }
    except Exception as e:
        return None

# Funzione On-Demand per gli Asset (scarica solo quando apri il menu)
@st.cache_data(ttl=3600)
def get_sub_assets_data(asset_list):
    try:
        # Scarica gruppo di 5 asset
        data = yf.download(asset_list, period="1y", group_by='ticker', progress=False)
        results = {}
        
        for t in asset_list:
            try:
                if len(asset_list) == 1:
                    df = data # Se è uno solo, la struttura è diversa
                    closes = df['Close']
                else:
                    df = data[t]
                    closes = df['Close']
                
                if len(closes) > 0:
                    curr = float(closes.iloc[-1])
                    sma20 = float(closes.rolling(20).mean().iloc[-1])
                    sma50 = float(closes.rolling(50).mean().iloc[-1])
                    sma200 = float(closes.rolling(200).mean().iloc[-1])
                    
                    results[t] = {
                        "price": curr,
                        "t_s": "🟢" if curr > sma20 else "🔴",
                        "t_m": "🟢" if curr > sma50 else "🔴",
                        "t_l": "🟢" if curr > sma200 else "🔴"
                    }
            except:
                continue
        return results
    except:
        return {}

# --- HELPER VISIVI ---
def color_val(val):
    c = "green" if val > 0 else "red"
    return f":{c}[{val:.1f}%]"

def render_score(curr, prev):
    c = "green" if curr > 0 else "red"
    arrow = "↗️" if curr > prev else "↘️"
    return f":{c}[**{curr:.1f}**] {arrow}"

# --- MAIN PAGE ---
st.title("🌍 Strategic Terminal v13.0 (Full Data)")

# 1. PREPARAZIONE DATI (BATCH)
# Raccogliamo tutti i Ticker Principali (Proxy)
all_proxies = [v['p'] for v in db['GEO'].values()] + \
              [v['p'] for v in db['SECTOR'].values()] + \
              [v['p'] for v in db['PILLARS'].values()]

with st.spinner("Connessione ai mercati globali (Batch Download)..."):
    # SCARICHIAMO TUTTO INSIEME QUI
    master_data = load_all_proxies(all_proxies)

if master_data is None or master_data.empty:
    st.error("Errore critico di connessione. Ricarica la pagina.")
    st.stop()

# --- HEADER STANDARD ---
def render_header():
    c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 1.5, 1])
    c1.markdown("### ASSET")
    c2.markdown("**SCORE**")
    c3.markdown("**1M**")
    c4.markdown("**3M**")
    c5.markdown("**STAGION.**")
    c6.markdown("**DETTAGLI**")
    st.divider()

# --- RENDER SEZIONE ---
def render_section(section_key, title):
    st.header(title)
    render_header()
    
    # Processiamo i dati dalla cache Batch
    rows = []
    for name, data in db[section_key].items():
        ticker = data['p']
        try:
            # Estrai dati dal Master Dataframe
            if len(all_proxies) > 1:
                df_asset = master_data[ticker]
            else:
                df_asset = master_data
            
            stats = calculate_stats(df_asset)
            if stats:
                rows.append({**stats, "Name": name, "Ticker": ticker, "Assets": data['assets']})
        except:
            continue
            
    # Ordina e Visualizza
    df_rows = pd.DataFrame(rows).sort_values(by="score", ascending=False)
    
    with st.container(height=600):
        for _, row in df_rows.iterrows():
            c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 1.5, 1])
            
            # Col 1: Nome + Icona Trend
            icon = "🔥" if row['score'] > 7.0 else ("❄️" if row['score'] < -7.0 else "")
            c1.markdown(f"**{icon} {row['Name']}**")
            
            # Dati
            c2.markdown(render_score(row['score'], row['score_prev']))
            c3.markdown(color_val(row['p1m']))
            c4.markdown(color_val(row['p3m']))
            c5.write(f"Best: **{row['best_month']}**")
            
            # Bottone Espansione
            key_exp = f"exp_{row['Ticker']}"
            btn_label = "⬇️ Mostra Asset" if st.session_state.get(key_exp) else "▶️ Mostra Asset"
            
            if c6.button(btn_label, key=f"btn_{row['Ticker']}"):
                # Toggle stato
                st.session_state[key_exp] = not st.session_state.get(key_exp, False)
                st.rerun()
            
            # SPACCATO INTERNO (Se espanso)
            if st.session_state.get(key_exp):
                with st.container(border=True):
                    # Scarica dati dei 5 asset SOLO ORA
                    with st.spinner(f"Analisi asset {row['Name']}..."):
                        sub_data = get_sub_assets_data(row['Assets'])
                    
                    if sub_data:
                        h1, h2, h3, h4, h5, h6 = st.columns([2, 1, 1, 1, 1, 1])
                        h1.markdown("*Ticker*")
                        h2.markdown("*Prezzo*")
                        h3.markdown("*Breve*")
                        h4.markdown("*Medio*")
                        h5.markdown("*Lungo*")
                        h6.markdown("*Grafico*")
                        
                        for t_sub in row['Assets']:
                            if t_sub in sub_data:
                                s = sub_data[t_sub]
                                sc1, sc2, sc3, sc4, sc5, sc6 = st.columns([2, 1, 1, 1, 1, 1])
                                sc1.write(f"**{t_sub}**")
                                sc2.write(f"${s['price']:.2f}")
                                sc3.write(s['t_s'])
                                sc4.write(s['t_m'])
                                sc5.write(s['t_l'])
                                sc6.link_button("📈", f"https://finance.yahoo.com/quote/{t_sub}")
                    else:
                        st.warning("Dati di dettaglio momentaneamente non disponibili.")
                st.divider()

# --- ESECUZIONE ---
render_section("GEO", "1. 🗺️ Analisi Geografica")
st.markdown("---")
render_section("SECTOR", "2. 🏭 Analisi Settoriale")
st.markdown("---")
render_section("PILLARS", "3. 🏛️ I 4 Pilastri")
