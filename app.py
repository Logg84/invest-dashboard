import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import calendar
import time
from datetime import datetime

# --- CONFIGURAZIONE VISIVA ---
st.set_page_config(page_title="Strategic Terminal v9.0 (Bulletproof)", layout="wide")

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

# --- DATABASE OTTIMIZZATO (TICKER PIÙ STABILI) ---
# Nota: Usiamo prevalentemente ETF USA (più dati, meno errori) per coprire le aree globali.
db_structure = {
    "GEO": {
        "USA (S&P 500)": { "proxy": "SPY", "assets": [{"t": "VOO", "n": "S&P 500"}, {"t": "QQQ", "n": "Nasdaq 100"}, {"t": "IWM", "n": "Russell 2000"}, {"t": "MSFT", "n": "Microsoft"}, {"t": "NVDA", "n": "Nvidia"}]},
        "India": { "proxy": "INDA", "assets": [{"t": "INDA", "n": "MSCI India ETF"}, {"t": "EPI", "n": "India Earnings ETF"}, {"t": "SMIN", "n": "India Small Cap"}, {"t": "INFY", "n": "Infosys (ADR)"}, {"t": "HDB", "n": "HDFC Bank (ADR)"}]},
        "Cina": { "proxy": "FXI", "assets": [{"t": "FXI", "n": "China Large-Cap"}, {"t": "KWEB", "n": "China Internet"}, {"t": "MCHI", "n": "MSCI China"}, {"t": "BABA", "n": "Alibaba"}, {"t": "PDD", "n": "PDD Holdings"}]},
        "Europa": { "proxy": "IEUR", "assets": [{"t": "VGK", "n": "FTSE Europe"}, {"t": "EZU", "n": "Eurozone ETF"}, {"t": "FEZ", "n": "Euro Stoxx 50"}, {"t": "NVO", "n": "Novo Nordisk"}, {"t": "ASML", "n": "ASML"}]},
        "Giappone": { "proxy": "EWJ", "assets": [{"t": "EWJ", "n": "MSCI Japan"}, {"t": "DXJ", "n": "Japan Hedged"}, {"t": "SONY", "n": "Sony Group"}, {"t": "TM", "n": "Toyota"}, {"t": "HMC", "n": "Honda"}]},
        "Germania": { "proxy": "EWG", "assets": [{"t": "EWG", "n": "Germany ETF"}, {"t": "DAX", "n": "Global X DAX"}, {"t": "SAP", "n": "SAP SE"}, {"t": "SIEGY", "n": "Siemens (ADR)"}, {"t": "DTEGY", "n": "Deutsche Tel. (ADR)"}]},
        "Regno Unito": { "proxy": "EWU", "assets": [{"t": "EWU", "n": "UK ETF"}, {"t": "FLGB", "n": "FTSE 100"}, {"t": "SHEL", "n": "Shell PLC"}, {"t": "HSBC", "n": "HSBC"}, {"t": "BP", "n": "BP PLC"}]},
        "Italia": { "proxy": "EWI", "assets": [{"t": "EWI", "n": "MSCI Italy ETF"}, {"t": "RACE", "n": "Ferrari"}, {"t": "STLA", "n": "Stellantis"}, {"t": "E", "n": "Eni SpA (ADR)"}, {"t": "IIALY", "n": "Intesa (ADR)"}]},
        "Brasile": { "proxy": "EWZ", "assets": [{"t": "EWZ", "n": "MSCI Brazil"}, {"t": "PBR", "n": "Petrobras"}, {"t": "VALE", "n": "Vale SA"}, {"t": "NU", "n": "Nu Holdings"}, {"t": "ITUB", "n": "Itau Unibanco"}]},
        "Taiwan": { "proxy": "EWT", "assets": [{"t": "EWT", "n": "MSCI Taiwan"}, {"t": "TSM", "n": "TSMC"}, {"t": "UMC", "n": "United Microelec."}, {"t": "ASX", "n": "ASE Tech"}, {"t": "IMOS", "n": "ChipMOS"}]},
        "Corea del Sud": { "proxy": "EWY", "assets": [{"t": "EWY", "n": "MSCI South Korea"}, {"t": "PKX", "n": "POSCO"}, {"t": "KB", "n": "KB Financial"}, {"t": "LPL", "n": "LG Display"}, {"t": "SKM", "n": "SK Telecom"}]},
        "Messico": { "proxy": "EWW", "assets": [{"t": "EWW", "n": "MSCI Mexico"}, {"t": "AMX", "n": "America Movil"}, {"t": "FMX", "n": "Fomento Economico"}, {"t": "VLRS", "n": "Volaris"}, {"t": "CX", "n": "Cemex"}]},
    },
    "SECTOR": {
        "Technology": { "proxy": "XLK", "assets": [{"t": "XLK", "n": "Tech Sector"}, {"t": "VGT", "n": "Vanguard IT"}, {"t": "MSFT", "n": "Microsoft"}, {"t": "AAPL", "n": "Apple"}, {"t": "ADBE", "n": "Adobe"}]},
        "Semiconductors": { "proxy": "SMH", "assets": [{"t": "SMH", "n": "VanEck Semi"}, {"t": "SOXX", "n": "iShares Semi"}, {"t": "NVDA", "n": "Nvidia"}, {"t": "AVGO", "n": "Broadcom"}, {"t": "AMD", "n": "AMD"}]},
        "Energy": { "proxy": "XLE", "assets": [{"t": "XLE", "n": "Energy Sector"}, {"t": "XOM", "n": "Exxon Mobil"}, {"t": "CVX", "n": "Chevron"}, {"t": "COP", "n": "ConocoPhillips"}, {"t": "EOG", "n": "EOG Resources"}]},
        "Healthcare": { "proxy": "XLV", "assets": [{"t": "XLV", "n": "Health Care"}, {"t": "LLY", "n": "Eli Lilly"}, {"t": "UNH", "n": "UnitedHealth"}, {"t": "JNJ", "n": "Johnson & Johnson"}, {"t": "ABBV", "n": "AbbVie"}]},
        "Financials": { "proxy": "XLF", "assets": [{"t": "XLF", "n": "Financials"}, {"t": "JPM", "n": "JPMorgan"}, {"t": "BAC", "n": "Bank of America"}, {"t": "WFC", "n": "Wells Fargo"}, {"t": "GS", "n": "Goldman Sachs"}]},
        "Defense": { "proxy": "ITA", "assets": [{"t": "ITA", "n": "Aerospace & Def"}, {"t": "XAR", "n": "Aerospace Equal W"}, {"t": "RTX", "n": "RTX Corp"}, {"t": "LMT", "n": "Lockheed Martin"}, {"t": "GD", "n": "General Dynamics"}]},
        "Gold Miners": { "proxy": "GDX", "assets": [{"t": "GDX", "n": "Gold Miners"}, {"t": "NEM", "n": "Newmont"}, {"t": "GOLD", "n": "Barrick Gold"}, {"t": "AEM", "n": "Agnico Eagle"}, {"t": "KGC", "n": "Kinross Gold"}]},
        "Uranium": { "proxy": "URA", "assets": [{"t": "URA", "n": "Global Uranium"}, {"t": "URNM", "n": "Sprott Uranium"}, {"t": "CCJ", "n": "Cameco"}, {"t": "UEC", "n": "Uranium Energy"}, {"t": "NXE", "n": "NexGen Energy"}]},
        "Cybersecurity": { "proxy": "CIBR", "assets": [{"t": "CIBR", "n": "Cybersecurity ETF"}, {"t": "HACK", "n": "Cyber ETF"}, {"t": "PANW", "n": "Palo Alto Net"}, {"t": "CRWD", "n": "CrowdStrike"}, {"t": "FTNT", "n": "Fortinet"}]},
        "Robotics & AI": { "proxy": "BOTZ", "assets": [{"t": "BOTZ", "n": "Robotics & AI"}, {"t": "ROBO", "n": "Robotics Auto"}, {"t": "PATH", "n": "UiPath"}, {"t": "ISRG", "n": "Intuitive Surgical"}, {"t": "TER", "n": "Teradyne"}]},
        "Biotech": { "proxy": "IBB", "assets": [{"t": "IBB", "n": "Biotech ETF"}, {"t": "XBI", "n": "Biotech SPDR"}, {"t": "VRTX", "n": "Vertex"}, {"t": "REGN", "n": "Regeneron"}, {"t": "AMGN", "n": "Amgen"}]},
        "Cons. Staples": { "proxy": "XLP", "assets": [{"t": "XLP", "n": "Staples ETF"}, {"t": "PG", "n": "Procter & Gamble"}, {"t": "COST", "n": "Costco"}, {"t": "PEP", "n": "PepsiCo"}, {"t": "KO", "n": "Coca-Cola"}]},
    },
    "PILLARS": {
        "1. DIFESA / AIRBAG": {
            "main": {"t": "GLD", "n": "SPDR Gold Shares (Oro Fisico)", "isin": "US78463V1070"},
            "alts": [
                {"t": "IAU", "n": "iShares Gold Trust", "isin": "US4642851053"},
                {"t": "SHY", "n": "iShares 1-3 Year Treasury Bond", "isin": "US4642874576"},
                {"t": "SLV", "n": "iShares Silver Trust", "isin": "US46428Q1094"}
            ]
        },
        "2. INFRA / REAL AI": {
            "main": {"t": "COPX", "n": "Global X Copper Miners", "isin": "US37954Y8306"},
            "alts": [
                {"t": "URA", "n": "Global X Uranium", "isin": "US37954Y8710"},
                {"t": "PAVE", "n": "US Infrastructure Dev", "isin": "US37950E3661"},
                {"t": "GRID", "n": "First Trust Smart Grid", "isin": "US33733E5092"}
            ]
        },
        "3. CICLICI / MOTORE": {
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

# --- MOTORE DI CALCOLO ROBUSTO (RETRY LOGIC) ---
def safe_download(ticker):
    """Scarica dati con tentativi multipli per evitare errori Yahoo"""
    max_retries = 3
    for i in range(max_retries):
        try:
            # Scarichiamo dati con thread disabilitati per stabilità
            df = yf.download(ticker, period="2y", progress=False, threads=False)
            if len(df) > 0:
                # FIX timezone
                if df.index.tz is not None:
                    df.index = df.index.tz_localize(None)
                return df
        except Exception:
            time.sleep(1) # Aspetta 1 secondo prima di riprovare
            continue
    return pd.DataFrame() # Ritorna vuoto se fallisce

@st.cache_data(ttl=3600) # Cache per 1 ora
def analyze_asset_complete(ticker):
    df = safe_download(ticker)
    
    if df.empty or len(df) < 20: 
        return None
    
    try:
        # Funzione helper calcolo score
        def calculate_score_on_subset(sub_df):
            if len(sub_df) < 20: return 0
            curr = float(sub_df['Close'].iloc[-1])
            def get_px(d): return float(sub_df['Close'].iloc[-d]) if len(sub_df) > d else float(sub_df['Close'].iloc[0])
            
            p1m, p3m, p6m, p1y = get_px(22), get_px(65), get_px(130), get_px(252)
            perf_1m = ((curr - p1m)/p1m)*100
            perf_3m = ((curr - p3m)/p3m)*100
            perf_6m = ((curr - p6m)/p6m)*100
            perf_1y = ((curr - p1y)/p1y)*100
            
            # Algoritmo Severo (Divisore 3.0)
            w_perf = (perf_3m*0.4) + (perf_1m*0.3) + (perf_6m*0.2) + (perf_1y*0.1)
            return max(min(w_perf / 3.0, 10), -10)

        # Score Attuale e Storici
        score_now = calculate_score_on_subset(df)
        
        idx_1m = -22 if len(df) > 22 else 0
        score_1m_ago = calculate_score_on_subset(df.iloc[:idx_1m])
        
        idx_3m = -65 if len(df) > 65 else 0
        score_3m_ago = calculate_score_on_subset(df.iloc[:idx_3m])
        
        # Trend Prezzo (SMA)
        curr_px = float(df['Close'].iloc[-1])
        sma20 = float(df['Close'].rolling(20).mean().iloc[-1])
        sma50 = float(df['Close'].rolling(50).mean().iloc[-1])
        sma200 = float(df['Close'].rolling(200).mean().iloc[-1])
        
        trend_short = "BULL" if curr_px > sma20 else "BEAR"
        trend_med = "BULL" if curr_px > sma50 else "BEAR"
        trend_long = "BULL" if curr_px > sma200 else "BEAR"
        
        # Stagionalità
        df['M'] = df.index.month
        monthly_avg = df.groupby('M')['Close'].pct_change().mean()
        best_month_idx = monthly_avg.idxmax()
        best_month_name = calendar.month_abbr[best_month_idx]

        return {
            "price": curr_px,
            "score": score_now,
            "score_prev_1m": score_1m_ago,
            "score_prev_3m": score_3m_ago,
            "trend_s": trend_short,
            "trend_m": trend_med,
            "trend_l": trend_long,
            "best_month": best_month_name
        }
    except Exception:
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
    st.title("🌍 Strategic Terminal v9.0")
    st.caption("Engine: Bulletproof Yahoo • Scoring: Direzionale & Severo")

    # HEADER TABELLA
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
    st.header("1. 🗺️ Analisi Geografica (Global Trend)")
    render_header()
    
    geo_list = []
    with st.spinner('Scaricamento dati globali (con retry)...'):
        for area, data in db_structure['GEO'].items():
            stats = analyze_asset_complete(data['proxy'])
            if stats: geo_list.append({**stats, "Area": area})
    
    if not geo_list:
        st.error("⚠️ Yahoo Finance non risponde. Ricarica la pagina tra 1 minuto.")
    else:
        df_geo = pd.DataFrame(geo_list).sort_values(by="score", ascending=False)
        
        with st.container(height=600):
            for _, row in df_geo.iterrows():
                c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 1.5, 1])
                
                # Nome con Icona
                icon = "🔥" if row['score'] > 7.0 else ("❄️" if row['score'] < -7.0 else "")
                c1.markdown(f"**{icon} {row['Area']}**")
                
                c2.markdown(render_score_cell(row['score'], row['score_prev_1m']))
                c3.write(f"{row['score_prev_1m']:.1f}")
                c4.write(f"{row['score_prev_3m']:.1f}")
                c5.write(f"Best: **{row['best_month']}**")
                
                lab = "⬇️" if st.session_state.expanded_geo == row['Area'] else "▶️"
                if c6.button(lab, key=f"bg_{row['Area']}"): toggle_geo(row['Area']); st.rerun()

                # SPACCATO (Top 5)
                if st.session_state.expanded_geo == row['Area']:
                    with st.container(border=True):
                        st.caption(f"Top Asset per: {row['Area']}")
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
    st.header("2. 🏭 Analisi Settoriale (GICS)")
    render_header()
    
    sect_list = []
    with st.spinner('Scaricamento dati settoriali...'):
        for sect, data in db_structure['SECTOR'].items():
            stats = analyze_asset_complete(data['proxy'])
            if stats: sect_list.append({**stats, "Settore": sect})
            
    if sect_list:
        df_sect = pd.DataFrame(sect_list).sort_values(by="score", ascending=False)
        with st.container(height=600):
            for _, row in df_sect.iterrows():
                c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 1.5, 1])
                icon = "🔥" if row['score'] > 7.0 else ("❄️" if row['score'] < -7.0 else "")
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
                        h1.markdown("*Asset*")
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

    # === SEZIONE 3: PILASTRI ===
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
                    if 'isin' in main: st.caption(f"ISIN: {main['isin']}")
                    
                    col_m1, col_m2 = st.columns(2)
                    col_m1.metric("Prezzo", f"${m_stats['price']:.0f}")
                    trend_icon = "🟢" if m_stats['trend_m'] == "BULL" else "🔴"
                    col_m2.metric("Trend (50d)", m_stats['trend_m'])
                
                st.divider()
                st.markdown("**Alternative:**")
                for alt in data['alts']:
                    st.write(f"🔹 **{alt['n']}**")
                    if 'isin' in alt: st.caption(f"ISIN: {alt['isin']}")
                    if st.button(f"Grafico {alt['t']}", key=f"alt_{alt['t']}"):
                        show_detail(alt['t'])
                        st.rerun()
        i += 1

# --- PAGINA DETTAGLIO ---
def render_detail():
    tk = st.session_state.selected_asset
    st.button("🔙 TORNA ALLA DASHBOARD", on_click=back_to_dash)
    st.title(f"Analisi Approfondita: {tk}")
    
    df = safe_download(tk)
    if not df.empty and len(df) > 20:
        st.subheader("Grafico Tecnico & Medie Mobili")
        df['SMA50'] = df['Close'].rolling(50).mean()
        df['SMA200'] = df['Close'].rolling(200).mean()
        st.line_chart(df[['Close', 'SMA50', 'SMA200']])
        
        st.subheader("Statistiche Chiave")
        curr = float(df['Close'].iloc[-1])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Prezzo Attuale", f"${curr:.2f}")
        c2.metric("Volatilità (Risk)", f"{df['Close'].pct_change().std()*np.sqrt(252)*100:.1f}%")
        
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
        st.error("Dati non disponibili per questo asset.")

# --- MAIN ---
if st.session_state.page == 'dashboard':
    render_dashboard()
else:
    render_detail()
