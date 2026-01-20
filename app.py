import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import calendar
from datetime import datetime, timedelta

# --- CONFIGURAZIONE VISIVA ---
st.set_page_config(page_title="Strategic Terminal v8.1", layout="wide")

st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 4px; height: 1.8em; padding: 0px; font-size: 0.8rem; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.3rem; }
    .trend-up { color: #00cc00; font-weight: bold; }
    .trend-down { color: #ff3333; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- STATO NAVIGAZIONE ---
if 'page' not in st.session_state: st.session_state.page = 'dashboard'
if 'selected_asset' not in st.session_state: st.session_state.selected_asset = None 
if 'expanded_geo' not in st.session_state: st.session_state.expanded_geo = None
if 'expanded_sector' not in st.session_state: st.session_state.expanded_sector = None

# --- DATABASE ESTESO (5 ASSET PER CATEGORIA) ---
db_structure = {
    "GEO": {
        "USA (S&P 500)": { 
            "proxy": "SPY", 
            "assets": [
                {"t": "VOO", "n": "Vanguard S&P 500", "type": "ETF", "isin": "IE00B3XXRP09"},
                {"t": "RSP", "n": "Invesco Equal Weight", "type": "ETF", "isin": "IE00BNGJJT35"},
                {"t": "QQQ", "n": "Invesco QQQ (Nasdaq)", "type": "ETF", "isin": "US46090E1038"},
                {"t": "MSFT", "n": "Microsoft Corp", "type": "Stock", "isin": "US5949181045"},
                {"t": "NVDA", "n": "NVIDIA Corp", "type": "Stock", "isin": "US67066G1040"}
            ]
        },
        "India": { 
            "proxy": "INDA", 
            "assets": [
                {"t": "INDA", "n": "iShares MSCI India", "type": "ETF", "isin": "IE00BZCQB185"},
                {"t": "EPI", "n": "WisdomTree India Earn.", "type": "ETF", "isin": "US97717W4226"},
                {"t": "FLIN", "n": "Franklin FTSE India", "type": "ETF", "isin": "IE00BHZRQZ17"},
                {"t": "RIGD.IL", "n": "Reliance Industries", "type": "Stock", "isin": "US7594701077"},
                {"t": "INFY", "n": "Infosys Ltd", "type": "Stock", "isin": "US4567881085"}
            ]
        },
        "Europa (Aggregate)": { 
            "proxy": "IEUR", 
            "assets": [
                {"t": "IEUR", "n": "iShares Core MSCI Europe", "type": "ETF", "isin": "IE00B4K48X80"},
                {"t": "VGK", "n": "Vanguard FTSE Europe", "type": "ETF", "isin": "US9220428745"},
                {"t": "FEZ", "n": "SPDR Euro Stoxx 50", "type": "ETF", "isin": "US78463X2027"},
                {"t": "ASML", "n": "ASML Holding", "type": "Stock", "isin": "USN070592100"},
                {"t": "NVO", "n": "Novo Nordisk", "type": "Stock", "isin": "US6701002056"}
            ]
        },
        "Giappone": { 
            "proxy": "EWJ", 
            "assets": [
                {"t": "EWJ", "n": "iShares MSCI Japan", "type": "ETF", "isin": "IE00B02KXH56"},
                {"t": "DXJ", "n": "WisdomTree Japan Hedged", "type": "ETF", "isin": "US97717W8516"},
                {"t": "BBJP", "n": "JPMorgan BetaBuilders Japan", "type": "ETF", "isin": "US46641Q3323"},
                {"t": "TM", "n": "Toyota Motor", "type": "Stock", "isin": "US8923313071"},
                {"t": "SONY", "n": "Sony Group", "type": "Stock", "isin": "US8356993076"}
            ]
        },
        "Cina": { 
            "proxy": "FXI", 
            "assets": [
                {"t": "FXI", "n": "iShares China Large-Cap", "type": "ETF", "isin": "IE00B02KXK85"},
                {"t": "KWEB", "n": "KraneShares CSI China Internet", "type": "ETF", "isin": "US5007673065"},
                {"t": "MCHI", "n": "iShares MSCI China", "type": "ETF", "isin": "US46429B6719"},
                {"t": "BABA", "n": "Alibaba Group", "type": "Stock", "isin": "US01609W1027"},
                {"t": "TCEHY", "n": "Tencent Holdings", "type": "Stock", "isin": "US88032Q1094"}
            ]
        },
        "Germania": { "proxy": "EWG", "assets": [{"t": "EWG", "n": "Germany ETF", "type": "ETF", "isin": "US4642868065"}, {"t": "DAX", "n": "DAX Index ETF", "type": "ETF", "isin": "DE0005933931"}, {"t": "SIE.DE", "n": "Siemens", "type": "Stock", "isin": "DE0007236101"}, {"t": "SAP", "n": "SAP SE", "type": "Stock", "isin": "DE0007164600"}, {"t": "DTE.DE", "n": "Deutsche Telekom", "type": "Stock", "isin": "DE0005557508"}]},
        "Regno Unito": { "proxy": "EWU", "assets": [{"t": "EWU", "n": "UK ETF", "type": "ETF", "isin": "US4642867075"}, {"t": "ISF.L", "n": "FTSE 100 ETF", "type": "ETF", "isin": "IE0005042456"}, {"t": "AZN", "n": "AstraZeneca", "type": "Stock", "isin": "US0463531089"}, {"t": "SHEL", "n": "Shell PLC", "type": "Stock", "isin": "US7802593050"}, {"t": "HSBC", "n": "HSBC Holdings", "type": "Stock", "isin": "US4042804066"}]},
        "Italia": { "proxy": "EWI", "assets": [{"t": "EWI", "n": "Italy ETF", "type": "ETF", "isin": "US4642867315"}, {"t": "ISP.MI", "n": "Intesa Sanpaolo", "type": "Stock", "isin": "IT0000072618"}, {"t": "ENI.MI", "n": "Eni SpA", "type": "Stock", "isin": "IT0003132476"}, {"t": "RACE", "n": "Ferrari NV", "type": "Stock", "isin": "NL0011585146"}, {"t": "UCG.MI", "n": "UniCredit", "type": "Stock", "isin": "IT0004781412"}]},
    },
    "SECTOR": {
        "Technology": { 
            "proxy": "XLK", 
            "assets": [
                {"t": "XLK", "n": "Technology Select Sector", "type": "ETF", "isin": "US81369Y8030"},
                {"t": "VGT", "n": "Vanguard Info Tech", "type": "ETF", "isin": "US92204A7028"},
                {"t": "MSFT", "n": "Microsoft", "type": "Stock", "isin": "US5949181045"},
                {"t": "AAPL", "n": "Apple Inc", "type": "Stock", "isin": "US0378331005"},
                {"t": "ORCL", "n": "Oracle", "type": "Stock", "isin": "US68389X1054"}
            ]
        },
        "Semiconductors": { 
            "proxy": "SMH", 
            "assets": [
                {"t": "SMH", "n": "VanEck Semiconductor", "type": "ETF", "isin": "US92189F6768"},
                {"t": "SOXX", "n": "iShares Semiconductor", "type": "ETF", "isin": "US4642875235"},
                {"t": "NVDA", "n": "Nvidia", "type": "Stock", "isin": "US67066G1040"},
                {"t": "AVGO", "n": "Broadcom", "type": "Stock", "isin": "US11135F1012"},
                {"t": "TSM", "n": "TSMC", "type": "Stock", "isin": "US8740391003"}
            ]
        },
        "Energy": { "proxy": "XLE", "assets": [{"t": "XLE", "n": "Energy Select", "type": "ETF", "isin": "US81369Y5069"}, {"t": "XOM", "n": "Exxon Mobil", "type": "Stock", "isin": "US30231G1022"}, {"t": "CVX", "n": "Chevron", "type": "Stock", "isin": "US1667641005"}, {"t": "SHEL", "n": "Shell", "type": "Stock", "isin": "US7802593050"}, {"t": "TTE", "n": "TotalEnergies", "type": "Stock", "isin": "US89151E1091"}]},
        "Healthcare": { "proxy": "XLV", "assets": [{"t": "XLV", "n": "Health Care Select", "type": "ETF", "isin": "US81369Y2090"}, {"t": "LLY", "n": "Eli Lilly", "type": "Stock", "isin": "US5324571083"}, {"t": "UNH", "n": "UnitedHealth", "type": "Stock", "isin": "US91324P1021"}, {"t": "JNJ", "n": "Johnson & Johnson", "type": "Stock", "isin": "US4781601046"}, {"t": "PFE", "n": "Pfizer", "type": "Stock", "isin": "US7170811035"}]},
        "Gold Miners": { "proxy": "GDX", "assets": [{"t": "GDX", "n": "VanEck Gold Miners", "type": "ETF", "isin": "US92189F1066"}, {"t": "GDXJ", "n": "Junior Gold Miners", "type": "ETF", "isin": "US92189F7915"}, {"t": "NEM", "n": "Newmont", "type": "Stock", "isin": "US6516391066"}, {"t": "GOLD", "n": "Barrick Gold", "type": "Stock", "isin": "CA0679011084"}, {"t": "AEM", "n": "Agnico Eagle", "type": "Stock", "isin": "CA0084741085"}]},
        "Defense": { "proxy": "ITA", "assets": [{"t": "ITA", "n": "US Aerospace & Def", "type": "ETF", "isin": "US4642887602"}, {"t": "PPA", "n": "Invesco Aerospace", "type": "ETF", "isin": "US46137V1008"}, {"t": "LMT", "n": "Lockheed Martin", "type": "Stock", "isin": "US5398301094"}, {"t": "RTX", "n": "RTX Corp", "type": "Stock", "isin": "US75513E1010"}, {"t": "LDO.MI", "n": "Leonardo", "type": "Stock", "isin": "IT0003856405"}]},
    },
    "PILLARS": {
        "1. DIFESA": {
            "main": {"t": "GLD", "n": "SPDR Gold Shares (Oro Fisico)", "isin": "US78463V1070"},
            "alts": [
                {"t": "IAU", "n": "iShares Gold Trust", "isin": "US4642851053"},
                {"t": "SHY", "n": "iShares 1-3 Year Treasury Bond", "isin": "US4642874576"},
                {"t": "SLV", "n": "iShares Silver Trust", "isin": "US46428Q1094"}
            ]
        },
        "2. INFRA / AI": {
            "main": {"t": "COPX", "n": "Global X Copper Miners", "isin": "US37954Y8306"},
            "alts": [
                {"t": "URA", "n": "Global X Uranium", "isin": "US37954Y8710"},
                {"t": "PAVE", "n": "US Infrastructure Dev", "isin": "US37950E3661"},
                {"t": "GRID", "n": "First Trust Smart Grid", "isin": "US33733E5092"}
            ]
        },
        "3. CICLICI": {
            "main": {"t": "IWM", "n": "iShares Russell 2000 (Small Cap)", "isin": "US4642876555"},
            "alts": [
                {"t": "VTV", "n": "Vanguard Value ETF", "isin": "US9229087443"},
                {"t": "IJR", "n": "iShares Core S&P Small-Cap", "isin": "US4642878049"},
                {"t": "EEM", "n": "iShares MSCI Emerging Markets", "isin": "US4642872349"}
            ]
        },
        "4. SPECULATIVI": {
            "main": {"t": "BTC-USD", "n": "Bitcoin (Spot Price)", "isin": "N/A"},
            "alts": [
                {"t": "ETH-USD", "n": "Ethereum (Spot Price)", "isin": "N/A"},
                {"t": "IBIT", "n": "iShares Bitcoin Trust", "isin": "US46438F1012"},
                {"t": "TQQQ", "n": "ProShares UltraPro QQQ (3x)", "isin": "US74347X8314"}
            ]
        }
    }
}

# --- MOTORE DI CALCOLO AVANZATO ---
@st.cache_data(ttl=3600)
def analyze_asset_complete(ticker):
    try:
        # Scarica più storico per calcolare i punteggi passati
        df = yf.download(ticker, period="2y", progress=False)
        if len(df) == 0: return None
        
        # FIX FUSO ORARIO PER EVITARE CRASH
        df.index = df.index.tz_localize(None)
        
        # Funzione helper per calcolare Score su un subset di dati
        def calculate_score_on_subset(sub_df):
            if len(sub_df) < 20: return 0
            curr = float(sub_df['Close'].iloc[-1])
            def get_px(d): return float(sub_df['Close'].iloc[-d]) if len(sub_df) > d else float(sub_df['Close'].iloc[0])
            
            p1m, p3m, p6m, p1y = get_px(22), get_px(65), get_px(130), get_px(252)
            perf_1m = ((curr - p1m)/p1m)*100
            perf_3m = ((curr - p3m)/p3m)*100
            perf_6m = ((curr - p6m)/p6m)*100
            perf_1y = ((curr - p1y)/p1y)*100
            
            # Algoritmo Severo
            w_perf = (perf_3m*0.4) + (perf_1m*0.3) + (perf_6m*0.2) + (perf_1y*0.1)
            return max(min(w_perf / 3.0, 10), -10)

        # Calcolo Score Attuale
        score_now = calculate_score_on_subset(df)
        
        # Calcolo Score 1 Mese fa (tagliamo il dataframe)
        idx_1m = -22 if len(df) > 22 else 0
        score_1m_ago = calculate_score_on_subset(df.iloc[:idx_1m])
        
        # Calcolo Score 3 Mesi fa
        idx_3m = -65 if len(df) > 65 else 0
        score_3m_ago = calculate_score_on_subset(df.iloc[:idx_3m])
        
        # Trend dello Score
        score_trend_1m = score_now - score_1m_ago
        
        # Trend Prezzo (Semplice per sub-menu)
        curr_px = float(df['Close'].iloc[-1])
        sma20 = float(df['Close'].rolling(20).mean().iloc[-1])
        sma50 = float(df['Close'].rolling(50).mean().iloc[-1])
        sma200 = float(df['Close'].rolling(200).mean().iloc[-1])
        
        trend_short = "BULL" if curr_px > sma20 else "BEAR"
        trend_med = "BULL" if curr_px > sma50 else "BEAR"
        trend_long = "BULL" if curr_px > sma200 else "BEAR"
        
        # Stagionalità (Mese migliore)
        df['M'] = df.index.month
        monthly_avg = df.groupby('M')['Close'].pct_change().mean()
        best_month_idx = monthly_avg.idxmax()
        best_month_name = calendar.month_abbr[best_month_idx]

        return {
            "price": curr_px,
            "score": score_now,
            "score_prev_1m": score_1m_ago,
            "score_prev_3m": score_3m_ago,
            "score_delta_1m": score_trend_1m,
            "trend_s": trend_short,
            "trend_m": trend_med,
            "trend_l": trend_long,
            "best_month": best_month_name
        }
    except Exception as e:
        return None

# --- NAVIGAZIONE ---
def show_detail(ticker):
    st.session_state.selected_asset = ticker
    st.session_state.page = 'detail'

def back_to_dash():
    st.session_state.page = 'dashboard'

def toggle_geo(area):
    st.session_state.expanded_geo = area if st.session_state.expanded_geo != area else None

def toggle_sector(sector):
    st.session_state.expanded_sector = sector if st.session_state.expanded_sector != sector else None

# --- UI HELPER ---
def render_score_cell(score_curr, score_prev):
    color = "green" if score_curr > 0 else "red"
    arrow = "↗️" if score_curr > score_prev else "↘️"
    return f":{color}[**{score_curr:.1f}**] {arrow}"

# --- PAGINA DASHBOARD ---
def render_dashboard():
    st.title("🌍 Strategic Terminal v8.1")
    st.markdown("Scoring Dinamico (Direzionalità) • Database Esteso • Fix Analisi")

    # HEADER TABELLA PRINCIPALE
    def render_header():
        c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 1.5, 1])
        c1.markdown("**ASSET / AREA**")
        c2.markdown("**SCORE**")
        c3.markdown("**1M AGO**")
        c4.markdown("**3M AGO**")
        c5.markdown("**STAGION.**")
        c6.markdown("**ACT**")
        st.divider()

    # === SEZIONE 1: GEOGRAFIA ===
    st.header("1. 🗺️ Analisi Geografica (Trend Score)")
    render_header()
    
    geo_list = []
    # Protezione se la lista è vuota
    with st.spinner('Calcolo Score Storici (Geografia)...'):
        for area, data in db_structure['GEO'].items():
            stats = analyze_asset_complete(data['proxy'])
            if stats: geo_list.append({**stats, "Area": area})
    
    if not geo_list:
        st.warning("⚠️ Impossibile scaricare i dati da Yahoo Finance al momento. Riprova tra qualche minuto.")
    else:
        df_geo = pd.DataFrame(geo_list).sort_values(by="score", ascending=False)
        
        with st.container(height=600):
            for _, row in df_geo.iterrows():
                c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 1.5, 1])
                
                # Nome con Icona
                icon = "🔥" if row['score'] > 7.5 else ("❄️" if row['score'] < -7.5 else "")
                c1.markdown(f"**{icon} {row['Area']}**")
                
                # Score Attuale e Passati
                c2.markdown(render_score_cell(row['score'], row['score_prev_1m']))
                c3.write(f"{row['score_prev_1m']:.1f}")
                c4.write(f"{row['score_prev_3m']:.1f}")
                
                # Stagionalità
                c5.write(f"Best: **{row['best_month']}**")
                
                # Bottone
                lab = "⬇️" if st.session_state.expanded_geo == row['Area'] else "▶️"
                if c6.button(lab, key=f"bg_{row['Area']}"): toggle_geo(row['Area']); st.rerun()

                # SPACCATO (SUB-MENU)
                if st.session_state.expanded_geo == row['Area']:
                    with st.container(border=True):
                        st.caption(f"Top 5 Asset per: {row['Area']}")
                        h1, h2, h3, h4, h5, h6 = st.columns([2, 1, 1, 1, 1, 1])
                        h1.markdown("*Nome Asset*")
                        h2.markdown("*Prezzo*")
                        h3.markdown("*Trend B.*")
                        h4.markdown("*Trend M.*")
                        h5.markdown("*Trend L.*")
                        
                        assets = db_structure['GEO'][row['Area']]['assets']
                        for a in assets:
                            s = analyze_asset_complete(a['t'])
                            if s:
                                ac1, ac2, ac3, ac4, ac5, ac6 = st.columns([2, 1, 1, 1, 1, 1])
                                ac1.write(f"**{a['n']}**")
                                ac2.write(f"${s['price']:.2f}")
                                
                                def t_col(t): return "🟢" if t=="BULL" else "🔴"
                                ac3.write(t_col(s['trend_s']))
                                ac4.write(t_col(s['trend_m']))
                                ac5.write(t_col(s['trend_l']))
                                
                                if ac6.button("📊", key=f"btn_g_{a['t']}"): show_detail(a['t']); st.rerun()
                    st.divider()

    st.markdown("---")

    # === SEZIONE 2: SETTORI ===
    st.header("2. 🏭 Analisi Settoriale (Trend Score)")
    render_header()
    
    sect_list = []
    with st.spinner('Calcolo Score Storici (Settori)...'):
        for sect, data in db_structure['SECTOR'].items():
            stats = analyze_asset_complete(data['proxy'])
            if stats: sect_list.append({**stats, "Settore": sect})
            
    if not sect_list:
        st.write("Dati settoriali non disponibili.")
    else:
        df_sect = pd.DataFrame(sect_list).sort_values(by="score", ascending=False)
        
        with st.container(height=600):
            for _, row in df_sect.iterrows():
                c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 1.5, 1])
                icon = "🔥" if row['score'] > 7.5 else ("❄️" if row['score'] < -7.5 else "")
                c1.markdown(f"**{icon} {row['Settore']}**")
                c2.markdown(render_score_cell(row['score'], row['score_prev_1m']))
                c3.write(f"{row['score_prev_1m']:.1f}")
                c4.write(f"{row['score_prev_3m']:.1f}")
                c5.write(f"Best: **{row['best_month']}**")
                
                lab = "⬇️" if st.session_state.expanded_sector == row['Settore'] else "▶️"
                if c6.button(lab, key=f"bs_{row['Settore']}"): toggle_sector(row['Settore']); st.rerun()

                if st.session_state.expanded_sector == row['Settore']:
                    with st.container(border=True):
                        h1, h2, h3, h4, h5, h6 = st.columns([2, 1, 1, 1, 1, 1])
                        h1.markdown("*Nome Asset*")
                        h2.markdown("*Trend B.*")
                        h3.markdown("*Trend M.*")
                        h4.markdown("*Trend L.*")
                        assets = db_structure['SECTOR'][row['Settore']]['assets']
                        for a in assets:
                            s = analyze_asset_complete(a['t'])
                            if s:
                                ac1, ac2, ac3, ac4, ac5, ac6 = st.columns([2, 1, 1, 1, 1, 1])
                                ac1.write(f"**{a['n']}**")
                                ac2.write(f"${s['price']:.2f}")
                                def t_col(t): return "🟢" if t=="BULL" else "🔴"
                                ac3.write(t_col(s['trend_s']))
                                ac4.write(t_col(s['trend_m']))
                                ac5.write(t_col(s['trend_l']))
                                if ac6.button("📊", key=f"btn_s_{a['t']}"): show_detail(a['t']); st.rerun()
                    st.divider()

    st.markdown("---")

    # === SEZIONE 3: I 4 PILASTRI ===
    st.header("3. 🏛️ I 4 Pilastri Strategici")
    
    cols = st.columns(4)
    i = 0
    for pillar_name, data in db_structure['PILLARS'].items():
        with cols[i]:
            with st.container(border=True):
                st.subheader(pillar_name)
                main = data['main']
                m_stats = analyze_asset_complete(main['t'])
                
                if m_stats:
                    st.markdown(f"**👑 {main['n']}**")
                    st.caption(f"ISIN: {main['isin']}")
                    
                    col_m1, col_m2 = st.columns(2)
                    col_m1.metric("Prezzo", f"${m_stats['price']:.0f}")
                    # Mostriamo il trend di medio termine
                    trend_icon = "🟢" if m_stats['trend_m'] == "BULL" else "🔴"
                    col_m2.metric("Trend (50d)", m_stats['trend_m'])
                
                st.divider()
                st.markdown("**Alternative:**")
                for alt in data['alts']:
                    st.write(f"🔹 **{alt['n']}**")
                    st.caption(f"ISIN: {alt['isin']}")
                    if st.button(f"Grafico {alt['t']}", key=f"alt_{alt['t']}"):
                        show_detail(alt['t'])
                        st.rerun()
        i += 1

# --- PAGINA DETTAGLIO (DEBUGGATA) ---
def render_detail():
    tk = st.session_state.selected_asset
    st.button("🔙 TORNA ALLA DASHBOARD", on_click=back_to_dash)
    st.title(f"Analisi Approfondita: {tk}")
    
    try:
        # Scarico dati e PULIZIA INDEX (Fix Crash)
        df = yf.download(tk, period="2y", progress=False)
        df.index = df.index.tz_localize(None) 
        
        if len(df) > 0:
            st.subheader("Grafico Tecnico & Medie Mobili")
            df['SMA50'] = df['Close'].rolling(50).mean()
            df['SMA200'] = df['Close'].rolling(200).mean()
            st.line_chart(df[['Close', 'SMA50', 'SMA200']])
            
            st.subheader("Statistiche Chiave")
            curr = float(df['Close'].iloc[-1])
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Prezzo Attuale", f"${curr:.2f}")
            c2.metric("Volatilità (Risk)", f"{df['Close'].pct_change().std()*np.sqrt(252)*100:.1f}%")
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            c3.metric("RSI (14)", f"{rsi:.1f}")
            c4.write("RSI < 30: Ipervenduto\nRSI > 70: Ipercomprato")
            
            st.subheader("📅 Stagionalità Mensile")
            df['M'] = df.index.month
            monthly = df.groupby('M')['Close'].apply(lambda x: (x.iloc[-1]-x.iloc[0])/x.iloc[0]*100)
            monthly.index = [calendar.month_abbr[i] for i in monthly.index]
            st.bar_chart(monthly)
        else:
            st.error("Nessun dato trovato per questo ticker.")
    except Exception as e:
        st.error(f"Errore nel caricamento del dettaglio: {e}")

# --- MAIN ---
if st.session_state.page == 'dashboard':
    render_dashboard()
else:
    render_detail()
