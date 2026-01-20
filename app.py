import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import calendar

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Strategic Terminal v4.0", layout="wide")

# --- STATO DELLA NAVIGAZIONE ---
if 'page' not in st.session_state: st.session_state.page = 'dashboard'
if 'selected_asset' not in st.session_state: st.session_state.selected_asset = None # Per il livello 3 (Grafici)
if 'expanded_sector' not in st.session_state: st.session_state.expanded_sector = None # Per il livello 2 (Lista Ticker)

# --- DATABASE STRUTTURATO ---
# Struttura: Categoria -> Proxy (per il ranking) -> Lista Asset (per l'investimento)
db_structure = {
    "GEO": {
        "Emerging Markets": {
            "proxy": "EEM",
            "assets": [
                {"t": "EEM", "n": "iShares MSCI Emerging Markets", "type": "ETF"},
                {"t": "VWO", "n": "Vanguard FTSE Emerging Mkt", "type": "ETF"},
                {"t": "TSM", "n": "Taiwan Semiconductor", "type": "Stock"},
                {"t": "TCEHY", "n": "Tencent Holdings", "type": "Stock"},
                {"t": "PBR", "n": "Petrobras", "type": "Stock"}
            ]
        },
        "India": {
            "proxy": "INDA",
            "assets": [
                {"t": "INDA", "n": "iShares MSCI India", "type": "ETF"},
                {"t": "EPI", "n": "WisdomTree India Earnings", "type": "ETF"},
                {"t": "RIGD.IL", "n": "Reliance Ind. (GDR)", "type": "Stock"},
                {"t": "IBN", "n": "ICICI Bank", "type": "Stock"},
                {"t": "TTM", "n": "Tata Motors", "type": "Stock"}
            ]
        },
        "USA (S&P 500)": {
            "proxy": "SPY",
            "assets": [
                {"t": "VOO", "n": "Vanguard S&P 500", "type": "ETF"},
                {"t": "RSP", "n": "Invesco Equal Weight", "type": "ETF"},
                {"t": "MSFT", "n": "Microsoft", "type": "Stock"},
                {"t": "NVDA", "n": "NVIDIA", "type": "Stock"},
                {"t": "BRK-B", "n": "Berkshire Hathaway", "type": "Stock"}
            ]
        },
        "Europa": {
            "proxy": "FEZ",
            "assets": [
                {"t": "FEZ", "n": "SPDR Euro Stoxx 50", "type": "ETF"},
                {"t": "VGK", "n": "Vanguard FTSE Europe", "type": "ETF"},
                {"t": "ASML", "n": "ASML Holding", "type": "Stock"},
                {"t": "SAP", "n": "SAP SE", "type": "Stock"},
                {"t": "MC.PA", "n": "LVMH", "type": "Stock"}
            ]
        },
        "Giappone": {
            "proxy": "EWJ",
            "assets": [
                {"t": "EWJ", "n": "iShares MSCI Japan", "type": "ETF"},
                {"t": "DXJ", "n": "WisdomTree Japan Hedged", "type": "ETF"},
                {"t": "TM", "n": "Toyota Motor", "type": "Stock"},
                {"t": "SONY", "n": "Sony Group", "type": "Stock"},
                {"t": "MFG", "n": "Mizuho Financial", "type": "Stock"}
            ]
        },
         "Cina": {
            "proxy": "FXI",
            "assets": [
                {"t": "FXI", "n": "iShares China Large-Cap", "type": "ETF"},
                {"t": "MCHI", "n": "iShares MSCI China", "type": "ETF"},
                {"t": "BABA", "n": "Alibaba", "type": "Stock"},
                {"t": "PDD", "n": "PDD Holdings", "type": "Stock"},
                {"t": "BIDU", "n": "Baidu", "type": "Stock"}
            ]
        }
    },
    "SECTOR": {
        "Technology & AI": {
            "proxy": "XLK",
            "assets": [
                {"t": "XLK", "n": "Technology Select Sector", "type": "ETF"},
                {"t": "SMH", "n": "VanEck Semiconductor", "type": "ETF"},
                {"t": "NVDA", "n": "NVIDIA", "type": "Stock"},
                {"t": "MSFT", "n": "Microsoft", "type": "Stock"},
                {"t": "PLTR", "n": "Palantir", "type": "Stock"}
            ]
        },
        "Energy & Uranium": {
            "proxy": "XLE",
            "assets": [
                {"t": "XLE", "n": "Energy Select Sector", "type": "ETF"},
                {"t": "URA", "n": "Global X Uranium", "type": "ETF"},
                {"t": "XOM", "n": "Exxon Mobil", "type": "Stock"},
                {"t": "CCJ", "n": "Cameco", "type": "Stock"},
                {"t": "URNM", "n": "Sprott Uranium Miners", "type": "ETF"}
            ]
        },
        "Gold Miners": {
            "proxy": "GDX",
            "assets": [
                {"t": "GDX", "n": "VanEck Gold Miners", "type": "ETF"},
                {"t": "GLD", "n": "SPDR Gold Shares (Fisico)", "type": "ETF"},
                {"t": "NEM", "n": "Newmont", "type": "Stock"},
                {"t": "GOLD", "n": "Barrick Gold", "type": "Stock"},
                {"t": "AEM", "n": "Agnico Eagle", "type": "Stock"}
            ]
        },
        "Aerospace & Defense": {
            "proxy": "ITA",
            "assets": [
                {"t": "ITA", "n": "iShares US Aerospace", "type": "ETF"},
                {"t": "PPA", "n": "Invesco Aerospace", "type": "ETF"},
                {"t": "LMT", "n": "Lockheed Martin", "type": "Stock"},
                {"t": "RTX", "n": "RTX Corp", "type": "Stock"},
                {"t": "LDO.MI", "n": "Leonardo SpA", "type": "Stock"}
            ]
        },
        "Healthcare": {
            "proxy": "XLV",
            "assets": [
                {"t": "XLV", "n": "Health Care Select", "type": "ETF"},
                {"t": "IBB", "n": "iShares Biotechnology", "type": "ETF"},
                {"t": "LLY", "n": "Eli Lilly", "type": "Stock"},
                {"t": "UNH", "n": "UnitedHealth", "type": "Stock"},
                {"t": "PFE", "n": "Pfizer", "type": "Stock"}
            ]
        }
    }
}

# --- FUNZIONI CALCOLO ---
@st.cache_data(ttl=3600)
def get_score_and_data(ticker):
    # Scarica dati e calcola punteggio sintetico
    df = yf.download(ticker, period="6mo", progress=False)
    if len(df) == 0: return None
    
    curr = float(df['Close'].iloc[-1])
    try:
        start_3m = float(df['Close'].iloc[-65])
        start_1m = float(df['Close'].iloc[-22])
    except:
        start_3m = float(df['Close'].iloc[0])
        start_1m = float(df['Close'].iloc[0])
        
    perf_3m = ((curr - start_3m) / start_3m) * 100
    perf_1m = ((curr - start_1m) / start_1m) * 100
    
    # Score da -10 a +10
    score = (perf_3m * 0.6) + (perf_1m * 0.4)
    score = max(min(score, 15), -15) # Cap visuale
    
    # Trend
    sma200 = df['Close'].rolling(200).mean().iloc[-1] if len(df) > 200 else start_3m
    trend = "BULL" if curr > sma200 else "BEAR"
    
    return {
        "price": curr,
        "score": score,
        "perf_1m": perf_1m,
        "trend": trend,
        "vol": float(df['Close'].pct_change().std() * np.sqrt(252) * 100)
    }

# --- NAVIGAZIONE ---
def show_detail(ticker):
    st.session_state.selected_asset = ticker
    st.session_state.page = 'detail'

def back_to_dash():
    st.session_state.page = 'dashboard'

def toggle_sector(sector_name):
    # Logica per aprire/chiudere lo spaccato
    if st.session_state.expanded_sector == sector_name:
        st.session_state.expanded_sector = None
    else:
        st.session_state.expanded_sector = sector_name

# --- PAGINA 1: DASHBOARD ---
def render_dashboard():
    st.title("🏛️ Investment Command Center v4")
    
    # === SEZIONE 1: CLASSIFICA GEOGRAFICA ===
    st.header("1. 🌍 Analisi Geografica (Classifica)")
    st.info("Clicca sul pulsante 'ESPANDI' per vedere i 5 asset migliori di quell'area.")
    
    # 1.1 Calcolo Ranking
    geo_ranking = []
    for area, data in db_structure['GEO'].items():
        stats = get_score_and_data(data['proxy'])
        if stats:
            geo_ranking.append({
                "Area": area,
                "Score": stats['score'],
                "Trend": stats['trend'],
                "Perf 1M": stats['perf_1m']
            })
    
    # Ordina dal migliore al peggiore
    df_geo = pd.DataFrame(geo_ranking).sort_values(by="Score", ascending=False)
    
    # 1.2 Visualizzazione Tabella + Bottone Espansione
    # Usiamo colonne per simulare una tabella interattiva
    col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([3, 1, 1, 1, 1])
    col_h1.markdown("**AREA GEOGRAFICA**")
    col_h2.markdown("**FORZA (-10/+10)**")
    col_h3.markdown("**TREND**")
    col_h4.markdown("**PERF 1M**")
    col_h5.markdown("**AZIONI**")
    st.divider()

    for index, row in df_geo.iterrows():
        c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
        c1.subheader(f"{index + 1}. {row['Area']}")
        
        # Colore Score
        score_color = "green" if row['Score'] > 0 else "red"
        c2.markdown(f":{score_color}[**{row['Score']:.1f}**]")
        c3.write(row['Trend'])
        c4.write(f"{row['Perf 1M']:.1f}%")
        
        # Bottone ESPANDI
        btn_label = "⬇️ CHIUDI" if st.session_state.expanded_sector == row['Area'] else "▶️ ESPANDI"
        if c5.button(btn_label, key=f"geo_btn_{row['Area']}"):
            toggle_sector(row['Area'])
            st.rerun() # Ricarica per mostrare l'espansione
            
        # 1.3 LIVELLO 2: SPACCATO (Se espanso)
        if st.session_state.expanded_sector == row['Area']:
            with st.container(border=True):
                st.markdown(f"#### 🔎 Spaccato Asset: {row['Area']}")
                st.markdown("Lista dei migliori strumenti (ETF e Azioni) per questa area. Clicca su **ANALISI** per i grafici.")
                
                # Intestazione Spaccato
                sc1, sc2, sc3, sc4, sc5 = st.columns([3, 1, 2, 2, 1])
                sc1.caption("NOME ASSET")
                sc2.caption("TIPO")
                sc3.caption("CONSIGLIO SISTEMA")
                sc4.caption("PREZZO")
                sc5.caption("AZIONE")
                
                assets = db_structure['GEO'][row['Area']]['assets']
                for asset in assets:
                    a_stats = get_score_and_data(asset['t'])
                    if a_stats:
                        sc1, sc2, sc3, sc4, sc5 = st.columns([3, 1, 2, 2, 1])
                        sc1.write(f"**{asset['n']}** ({asset['t']})")
                        sc2.write(asset['type'])
                        
                        # Calcolo Segnale Semplice
                        signal = "🟢 BUY" if a_stats['score'] > 2 else ("🔴 SELL" if a_stats['score'] < -2 else "🟡 HOLD")
                        sc3.write(signal)
                        sc4.write(f"${a_stats['price']:.2f}")
                        
                        if sc5.button("📊", key=f"det_{asset['t']}"):
                            show_detail(asset['t'])
                            st.rerun()
                st.divider()

    st.markdown("---")

    # === SEZIONE 2: CLASSIFICA SETTORIALE ===
    st.header("2. 🏭 Analisi Settoriale (Classifica)")
    
    # 2.1 Calcolo Ranking
    sect_ranking = []
    for sector, data in db_structure['SECTOR'].items():
        stats = get_score_and_data(data['proxy'])
        if stats:
            sect_ranking.append({
                "Settore": sector,
                "Score": stats['score'],
                "Trend": stats['trend'],
                "Perf 1M": stats['perf_1m']
            })
            
    df_sect = pd.DataFrame(sect_ranking).sort_values(by="Score", ascending=False)
    
    # 2.2 Visualizzazione
    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns([3, 1, 1, 1, 1])
    col_s1.markdown("**SETTORE**")
    col_s2.markdown("**FORZA**")
    col_s3.markdown("**TREND**")
    col_s4.markdown("**PERF 1M**")
    col_s5.markdown("**AZIONI**")
    st.divider()

    for index, row in df_sect.iterrows():
        c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
        c1.subheader(f"{index + 1}. {row['Settore']}")
        score_color = "green" if row['Score'] > 0 else "red"
        c2.markdown(f":{score_color}[**{row['Score']:.1f}**]")
        c3.write(row['Trend'])
        c4.write(f"{row['Perf 1M']:.1f}%")
        
        btn_label = "⬇️ CHIUDI" if st.session_state.expanded_sector == row['Settore'] else "▶️ ESPANDI"
        if c5.button(btn_label, key=f"sec_btn_{row['Settore']}"):
            toggle_sector(row['Settore'])
            st.rerun()

        # 2.3 SPACCATO
        if st.session_state.expanded_sector == row['Settore']:
            with st.container(border=True):
                st.markdown(f"#### 🔎 Spaccato Asset: {row['Settore']}")
                
                sc1, sc2, sc3, sc4, sc5 = st.columns([3, 1, 2, 2, 1])
                sc1.caption("NOME ASSET")
                sc2.caption("TIPO")
                sc3.caption("CONSIGLIO")
                sc4.caption("PREZZO")
                
                assets = db_structure['SECTOR'][row['Settore']]['assets']
                for asset in assets:
                    a_stats = get_score_and_data(asset['t'])
                    if a_stats:
                        sc1, sc2, sc3, sc4, sc5 = st.columns([3, 1, 2, 2, 1])
                        sc1.write(f"**{asset['n']}**")
                        sc2.write(asset['type'])
                        signal = "🟢 BUY" if a_stats['score'] > 2 else ("🔴 SELL" if a_stats['score'] < -2 else "🟡 HOLD")
                        sc3.write(signal)
                        sc4.write(f"${a_stats['price']:.2f}")
                        if sc5.button("📊", key=f"det_sec_{asset['t']}"):
                            show_detail(asset['t'])
                            st.rerun()
                st.divider()
    
    st.markdown("---")

    # === SEZIONE 3: I 4 PILASTRI ===
    st.header("3. 🏛️ Stato dei 4 Pilastri")
    col1, col2, col3, col4 = st.columns(4)
    
    pillars = [
        {"name": "1. ORO (Difesa)", "t": "GLD"},
        {"name": "2. RAME (Infra)", "t": "COPX"},
        {"name": "3. SMALL CAP (Ciclo)", "t": "IWM"},
        {"name": "4. BITCOIN (Risk)", "t": "BTC-USD"}
    ]
    
    cols = [col1, col2, col3, col4]
    for i, p in enumerate(pillars):
        stats = get_score_and_data(p['t'])
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"**{p['name']}**")
                if stats:
                    color = "green" if stats['trend'] == "BULL" else "red"
                    st.metric("Trend", stats['trend'], f"{stats['perf_1m']:.1f}%")
                    st.caption(f"Forza: {stats['score']:.1f}/10")
                    if stats['trend'] == "BULL":
                        st.success("ACCUMULARE")
                    else:
                        st.error("RIDURRE/ATTENDERE")

    # === SEZIONE 4: RADAR EMERGENTI ===
    st.markdown("---")
    st.header("4. 📡 Radar Trend Emergenti (Watchlist)")
    
    radar_assets = [
        {"n": "Cybersecurity", "t": "CIBR", "desc": "Sicurezza Digitale"},
        {"n": "Robotics", "t": "ROBO", "desc": "Automazione Industriale"},
        {"n": "Clean Energy Grid", "t": "ICLN", "desc": "Rete Elettrica Smart"}
    ]
    
    r_cols = st.columns(3)
    for i, r in enumerate(radar_assets):
        stats = get_score_and_data(r['t'])
        with r_cols[i]:
            st.subheader(r['n'])
            st.caption(r['desc'])
            if stats:
                st.write(f"Trend: **{stats['trend']}**")
                if st.button(f"Analizza {r['n']}", key=f"rad_{r['t']}"):
                    show_detail(r['t'])
                    st.rerun()

# --- PAGINA 2: DETTAGLIO ASSET (Livello 3) ---
def render_detail_page():
    ticker = st.session_state.selected_asset
    st.button("🔙 TORNA ALLA LISTA", on_click=back_to_dash)
    
    st.title(f"Analisi Approfondita: {ticker}")
    
    # Dati
    stock = yf.Ticker(ticker)
    df = stock.history(period="2y")
    info = stock.info
    
    if df.empty:
        st.error("Errore caricamento dati.")
        return

    # Header
    curr = df['Close'].iloc[-1]
    prev = df['Close'].iloc[-2]
    delta = ((curr - prev)/prev)*100
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Prezzo Attuale", f"${curr:.2f}", f"{delta:.2f}%")
    c2.metric("Massimo 52 Sett.", info.get('fiftyTwoWeekHigh', 'N/A'))
    c3.metric("Minimo 52 Sett.", info.get('fiftyTwoWeekLow', 'N/A'))
    
    # Grafico
    st.subheader("Grafico Tecnico (Con Media Mobile 50/200)")
    df['SMA50'] = df['Close'].rolling(50).mean()
    df['SMA200'] = df['Close'].rolling(200).mean()
    st.line_chart(df[['Close', 'SMA50', 'SMA200']], color=["#ffffff", "#00ff00", "#ff0000"])
    
    # Stagionalità
    st.subheader("📅 Stagionalità Storica")
    st.caption("Barre alte = Mese storicamente positivo.")
    df_seas = df.copy()
    df_seas['M'] = df_seas.index.month
    monthly = df_seas.groupby('M')['Close'].apply(lambda x: (x.iloc[-1]-x.iloc[0])/x.iloc[0]*100)
    monthly.index = [calendar.month_name[i] for i in monthly.index]
    st.bar_chart(monthly)
    
    # Descrizione
    with st.expander("📖 Leggi Descrizione Azienda/ETF"):
        st.write(info.get('longBusinessSummary', 'Nessuna descrizione disponibile.'))

# --- MAIN LOOP ---
if st.session_state.page == 'dashboard':
    render_dashboard()
else:
    render_detail_page()
