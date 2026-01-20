import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import calendar

# --- CONFIGURAZIONE VISIVA ---
st.set_page_config(page_title="Strategic Terminal v7.0 (Strict)", layout="wide")

st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 5px; height: 2em; padding: 0.1em; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# --- STATO NAVIGAZIONE ---
if 'page' not in st.session_state: st.session_state.page = 'dashboard'
if 'selected_asset' not in st.session_state: st.session_state.selected_asset = None 
if 'expanded_geo' not in st.session_state: st.session_state.expanded_geo = None
if 'expanded_sector' not in st.session_state: st.session_state.expanded_sector = None

# --- DATABASE ---
db_structure = {
    "GEO": {
        "USA (S&P 500)": { "proxy": "SPY", "assets": [{"t": "VOO", "n": "S&P 500", "type": "ETF"}, {"t": "QQQ", "n": "Nasdaq", "type": "ETF"}]},
        "USA (Dow Jones)": { "proxy": "DIA", "assets": [{"t": "DIA", "n": "Dow Jones", "type": "ETF"}, {"t": "BA", "n": "Boeing", "type": "Stock"}]},
        "Cina": { "proxy": "FXI", "assets": [{"t": "FXI", "n": "China Large-Cap", "type": "ETF"}, {"t": "BABA", "n": "Alibaba", "type": "Stock"}]},
        "India": { "proxy": "INDA", "assets": [{"t": "INDA", "n": "India ETF", "type": "ETF"}, {"t": "EPI", "n": "India Earnings", "type": "ETF"}]},
        "Giappone": { "proxy": "EWJ", "assets": [{"t": "EWJ", "n": "Japan ETF", "type": "ETF"}, {"t": "TM", "n": "Toyota", "type": "Stock"}]},
        "Germania": { "proxy": "EWG", "assets": [{"t": "EWG", "n": "Germany ETF", "type": "ETF"}, {"t": "DAX", "n": "DAX Index", "type": "ETF"}]},
        "Regno Unito": { "proxy": "EWU", "assets": [{"t": "EWU", "n": "UK ETF", "type": "ETF"}, {"t": "SHEL", "n": "Shell", "type": "Stock"}]},
        "Francia": { "proxy": "EWQ", "assets": [{"t": "EWQ", "n": "France ETF", "type": "ETF"}, {"t": "MC.PA", "n": "LVMH", "type": "Stock"}]},
        "Italia": { "proxy": "EWI", "assets": [{"t": "EWI", "n": "Italy ETF", "type": "ETF"}, {"t": "ISP.MI", "n": "Intesa", "type": "Stock"}]},
        "Svizzera": { "proxy": "EWL", "assets": [{"t": "EWL", "n": "Switzerland ETF", "type": "ETF"}, {"t": "NESN.SW", "n": "Nestle", "type": "Stock"}]},
        "Taiwan": { "proxy": "EWT", "assets": [{"t": "EWT", "n": "Taiwan ETF", "type": "ETF"}, {"t": "TSM", "n": "TSMC", "type": "Stock"}]},
        "Corea del Sud": { "proxy": "EWY", "assets": [{"t": "EWY", "n": "Korea ETF", "type": "ETF"}, {"t": "005930.KS", "n": "Samsung", "type": "Stock"}]},
        "Brasile": { "proxy": "EWZ", "assets": [{"t": "EWZ", "n": "Brazil ETF", "type": "ETF"}, {"t": "PBR", "n": "Petrobras", "type": "Stock"}]},
        "Messico": { "proxy": "EWW", "assets": [{"t": "EWW", "n": "Mexico ETF", "type": "ETF"}, {"t": "AMX", "n": "America Movil", "type": "Stock"}]},
        "Canada": { "proxy": "EWC", "assets": [{"t": "EWC", "n": "Canada ETF", "type": "ETF"}, {"t": "RY", "n": "Royal Bank", "type": "Stock"}]},
        "Australia": { "proxy": "EWA", "assets": [{"t": "EWA", "n": "Australia ETF", "type": "ETF"}, {"t": "BHP", "n": "BHP", "type": "Stock"}]},
        "Paesi Bassi": { "proxy": "EWN", "assets": [{"t": "EWN", "n": "Netherlands", "type": "ETF"}, {"t": "ASML", "n": "ASML", "type": "Stock"}]},
        "Spagna": { "proxy": "EWP", "assets": [{"t": "EWP", "n": "Spain ETF", "type": "ETF"}, {"t": "BBVA", "n": "BBVA", "type": "Stock"}]},
        "Svezia": { "proxy": "EWD", "assets": [{"t": "EWD", "n": "Sweden ETF", "type": "ETF"}, {"t": "ERIC", "n": "Ericsson", "type": "Stock"}]},
        "Turchia": { "proxy": "TUR", "assets": [{"t": "TUR", "n": "Turkey ETF", "type": "ETF"}, {"t": "TKC", "n": "Turkcell", "type": "Stock"}]}
    },
    "SECTOR": {
        "Technology": {"proxy": "XLK", "assets": [{"t": "XLK", "n": "Tech ETF", "type": "ETF"}, {"t": "MSFT", "n": "Microsoft", "type": "Stock"}]},
        "Semiconductors": {"proxy": "SMH", "assets": [{"t": "SMH", "n": "Semis ETF", "type": "ETF"}, {"t": "NVDA", "n": "Nvidia", "type": "Stock"}]},
        "Aerospace & Def": {"proxy": "ITA", "assets": [{"t": "ITA", "n": "Defense ETF", "type": "ETF"}, {"t": "LMT", "n": "Lockheed", "type": "Stock"}]},
        "Energy": {"proxy": "XLE", "assets": [{"t": "XLE", "n": "Energy ETF", "type": "ETF"}, {"t": "XOM", "n": "Exxon", "type": "Stock"}]},
        "Financials": {"proxy": "XLF", "assets": [{"t": "XLF", "n": "Financial ETF", "type": "ETF"}, {"t": "JPM", "n": "JPMorgan", "type": "Stock"}]},
        "Healthcare": {"proxy": "XLV", "assets": [{"t": "XLV", "n": "Health ETF", "type": "ETF"}, {"t": "LLY", "n": "Eli Lilly", "type": "Stock"}]},
        "Industrials": {"proxy": "XLI", "assets": [{"t": "XLI", "n": "Industrial ETF", "type": "ETF"}, {"t": "CAT", "n": "Caterpillar", "type": "Stock"}]},
        "Utilities": {"proxy": "XLU", "assets": [{"t": "XLU", "n": "Utilities ETF", "type": "ETF"}, {"t": "NEE", "n": "NextEra", "type": "Stock"}]},
        "Materials": {"proxy": "XLB", "assets": [{"t": "XLB", "n": "Materials ETF", "type": "ETF"}, {"t": "LIN", "n": "Linde", "type": "Stock"}]},
        "Real Estate": {"proxy": "XLRE", "assets": [{"t": "XLRE", "n": "Real Estate ETF", "type": "ETF"}, {"t": "PLD", "n": "Prologis", "type": "Stock"}]},
        "Cons. Staples": {"proxy": "XLP", "assets": [{"t": "XLP", "n": "Staples ETF", "type": "ETF"}, {"t": "PG", "n": "Procter & Gamble", "type": "Stock"}]},
        "Cons. Discret.": {"proxy": "XLY", "assets": [{"t": "XLY", "n": "Discret. ETF", "type": "ETF"}, {"t": "AMZN", "n": "Amazon", "type": "Stock"}]},
        "Comm. Services": {"proxy": "XLC", "assets": [{"t": "XLC", "n": "Comm. ETF", "type": "ETF"}, {"t": "GOOGL", "n": "Google", "type": "Stock"}]},
        "Gold Miners": {"proxy": "GDX", "assets": [{"t": "GDX", "n": "Gold Miners", "type": "ETF"}, {"t": "NEM", "n": "Newmont", "type": "Stock"}]},
        "Biotech": {"proxy": "IBB", "assets": [{"t": "IBB", "n": "Biotech ETF", "type": "ETF"}, {"t": "VRTX", "n": "Vertex", "type": "Stock"}]},
        "Regional Banking": {"proxy": "KRE", "assets": [{"t": "KRE", "n": "Regional Bank", "type": "ETF"}, {"t": "USB", "n": "US Bancorp", "type": "Stock"}]}
    },
    "PILLARS": {
        "1. DIFESA / AIRBAG": {
            "main": {"t": "GLD", "n": "Oro Fisico"},
            "alts": [{"t": "SHY", "n": "Bond USA 1-3Y"}, {"t": "SLV", "n": "Argento"}]
        },
        "2. INFRA / REAL AI": {
            "main": {"t": "COPX", "n": "Rame Miners"},
            "alts": [{"t": "URA", "n": "Uranio"}, {"t": "PAVE", "n": "Infrastrutture"}]
        },
        "3. CICLICI / MOTORE": {
            "main": {"t": "IWM", "n": "Small Caps USA"},
            "alts": [{"t": "VTV", "n": "Value Stocks"}, {"t": "EEM", "n": "Emerging Mkts"}]
        },
        "4. SPECULATIVI": {
            "main": {"t": "BTC-USD", "n": "Bitcoin"},
            "alts": [{"t": "ETH-USD", "n": "Ethereum"}, {"t": "QQQ", "n": "Nasdaq 100"}]
        }
    }
}

# --- MOTORE DI CALCOLO (ALGORITMO SEVERO) ---
@st.cache_data(ttl=3600)
def get_extended_data(ticker):
    try:
        df = yf.download(ticker, period="2y", progress=False)
        if len(df) == 0: return None
        
        curr = float(df['Close'].iloc[-1])
        
        def get_past_price(days):
            idx = -days if len(df) > days else 0
            return float(df['Close'].iloc[idx])

        p1m = get_past_price(22)
        p3m = get_past_price(65)
        p6m = get_past_price(130)
        p1y = get_past_price(252)
        
        perf_1m = ((curr - p1m) / p1m) * 100
        perf_3m = ((curr - p3m) / p3m) * 100
        perf_6m = ((curr - p6m) / p6m) * 100
        perf_1y = ((curr - p1y) / p1y) * 100
        
        # --- NEW SCORING ALGORITHM (STRICT MODE) ---
        # Vecchio metodo: somma ponderata diretta.
        # Nuovo metodo: La somma ponderata viene divisa per un fattore di difficoltà (3.0)
        # Esempio: Se un asset fa +10% su tutti i timeframe, il weighted è 10.
        # Score finale = 10 / 3 = 3.3 (Voto basso/realistico)
        # Per avere 10, devi avere una media pesata del 30%+.
        
        weighted_perf = (perf_3m * 0.4) + (perf_1m * 0.3) + (perf_6m * 0.2) + (perf_1y * 0.1)
        raw_score = weighted_perf / 3.0 
        
        # Cap a +/- 10
        score = max(min(raw_score, 10), -10)
        
        sma200_val = float(df['Close'].rolling(200).mean().iloc[-1]) if len(df) > 200 else p6m
        trend = "BULL" if curr > sma200_val else "BEAR"
        
        return {"price": curr, "score": score, "trend": trend, "p1m": perf_1m, "p3m": perf_3m, "p6m": perf_6m, "p1y": perf_1y}
    except:
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

# --- UI COMPONENTS ---
def render_header_row():
    c1, c2, c3, c4, c5, c6, c7 = st.columns([2.5, 1, 1, 1, 1, 1, 1])
    c1.markdown("**NOME ASSET**")
    c2.markdown("**1M**")
    c3.markdown("**3M**")
    c4.markdown("**6M**")
    c5.markdown("**1A**")
    c6.markdown("**SCORE**")
    c7.markdown("**ACT**")
    return c1, c2, c3, c4, c5, c6, c7

def color_val(val):
    return f":green[{val:.1f}%]" if val > 0 else f":red[{val:.1f}%]"

def render_list_item(name, stats, expanded_key, toggle_func, type_label):
    # Logica Icone integrata (Niente righe doppie)
    icon_prefix = ""
    # Soglia alzata a 8.0 per rendere il "FIRE" esclusivo
    if stats['score'] >= 8.0:
        icon_prefix = "🔥 " 
    elif stats['score'] <= -8.0:
        icon_prefix = "❄️ "
        
    c1, c2, c3, c4, c5, c6, c7 = st.columns([2.5, 1, 1, 1, 1, 1, 1])
    
    # Riga Unica Pulita
    c1.markdown(f"**{icon_prefix}{name}**")
    c2.markdown(color_val(stats['p1m']))
    c3.markdown(color_val(stats['p3m']))
    c4.markdown(color_val(stats['p6m']))
    c5.markdown(color_val(stats['p1y']))
    
    score_color = "green" if stats['score'] > 0 else "red"
    # Grassetto per lo score
    c6.markdown(f":{score_color}[**{stats['score']:.1f}**]")
    
    label = "⬇️" if expanded_key == name else "▶️"
    if c7.button(label, key=f"btn_{type_label}_{name}"):
        toggle_func(name)
        st.rerun()

# --- PAGINA DASHBOARD ---
def render_dashboard():
    st.title("🌍 Strategic Investment Terminal v7.0")
    st.caption("Scoring Algoritmico Severo (Scala /3) • Ordine per Forza Relativa")

    # === SEZIONE 1: GEOGRAFIA ===
    st.header("1. 🗺️ Analisi Geografica (Global Ranking)")
    render_header_row()
    st.divider()

    geo_list = []
    with st.spinner('Scaricamento dati macro...'):
        for area, data in db_structure['GEO'].items():
            stats = get_extended_data(data['proxy'])
            if stats: geo_list.append({**stats, "Area": area})
    
    df_geo = pd.DataFrame(geo_list).sort_values(by="score", ascending=False)

    with st.container(height=600): # Aumentata altezza per vedere più stati
        for _, row in df_geo.iterrows():
            render_list_item(row['Area'], row, st.session_state.expanded_geo, toggle_geo, "geo")
            
            if st.session_state.expanded_geo == row['Area']:
                with st.container(border=True):
                    st.caption(f"Strumenti per: {row['Area']}")
                    assets = db_structure['GEO'][row['Area']]['assets']
                    
                    h1, h2, h3, h4 = st.columns([3, 2, 2, 1])
                    h1.markdown("*Asset*")
                    h2.markdown("*Prezzo*")
                    h3.markdown("*Trend*")
                    
                    for asset in assets:
                        astats = get_extended_data(asset['t'])
                        if astats:
                            ac1, ac2, ac3, ac4 = st.columns([3, 2, 2, 1])
                            ac1.write(f"**{asset['n']}**")
                            ac2.write(f"${astats['price']:.2f}")
                            trend_icon = "🟢" if astats['trend'] == "BULL" else "🔴"
                            ac3.write(f"{trend_icon} {astats['trend']}")
                            if ac4.button("📊", key=f"d_g_{asset['t']}"):
                                show_detail(asset['t'])
                                st.rerun()
                st.divider()

    st.markdown("---")

    # === SEZIONE 2: SETTORI ===
    st.header("2. 🏭 Analisi Settoriale (GICS Ranking)")
    render_header_row()
    st.divider()
    
    sect_list = []
    with st.spinner('Scansione settoriale...'):
        for sect, data in db_structure['SECTOR'].items():
            stats = get_extended_data(data['proxy'])
            if stats: sect_list.append({**stats, "Settore": sect})
            
    df_sect = pd.DataFrame(sect_list).sort_values(by="score", ascending=False)
    
    with st.container(height=600):
        for _, row in df_sect.iterrows():
            render_list_item(row['Settore'], row, st.session_state.expanded_sector, toggle_sector, "sect")
            
            if st.session_state.expanded_sector == row['Settore']:
                with st.container(border=True):
                    assets = db_structure['SECTOR'][row['Settore']]['assets']
                    h1, h2, h3, h4 = st.columns([3, 2, 2, 1])
                    h1.markdown("*Asset*")
                    h2.markdown("*Prezzo*")
                    h3.markdown("*Trend*")
                    
                    for asset in assets:
                        astats = get_extended_data(asset['t'])
                        if astats:
                            ac1, ac2, ac3, ac4 = st.columns([3, 2, 2, 1])
                            ac1.write(f"**{asset['n']}**")
                            ac2.write(f"${astats['price']:.2f}")
                            trend_icon = "🟢" if astats['trend'] == "BULL" else "🔴"
                            ac3.write(f"{trend_icon} {astats['trend']}")
                            if ac4.button("📊", key=f"d_s_{asset['t']}"):
                                show_detail(asset['t'])
                                st.rerun()
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
                m_stats = get_extended_data(main['t'])
                
                if m_stats:
                    st.markdown(f"**👑 Main: {main['n']}**")
                    col_m1, col_m2 = st.columns(2)
                    col_m1.metric("Prezzo", f"${m_stats['price']:.0f}")
                    col_m2.metric("Trend", m_stats['trend'], f"{m_stats['p1m']:.1f}%")
                    
                    if m_stats['trend'] == "BULL": st.success("ACCUMULARE")
                    else: st.error("RIDURRE")
                
                st.divider()
                st.markdown("**Alternative:**")
                for alt in data['alts']:
                    a_stats = get_extended_data(alt['t'])
                    if a_stats:
                        icon = "🟢" if a_stats['trend'] == "BULL" else "🔴"
                        st.write(f"{icon} **{alt['n']}**: {a_stats['p1m']:.1f}%")
                        if st.button(f"Analizza {alt['t']}", key=f"alt_{alt['t']}"):
                            show_detail(alt['t'])
                            st.rerun()
        i += 1

# --- PAGINA DETTAGLIO ---
def render_detail():
    tk = st.session_state.selected_asset
    st.button("🔙 TORNA ALLA DASHBOARD", on_click=back_to_dash)
    st.title(f"Analisi Approfondita: {tk}")
    
    try:
        df = yf.download(tk, period="2y", progress=False)
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
            
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            c3.metric("RSI (14)", f"{rsi:.1f}")
            c4.write("RSI < 30: Ipervenduto\nRSI > 70: Ipercomprato")
            
            st.subheader("📅 Stagionalità")
            df['M'] = df.index.month
            monthly = df.groupby('M')['Close'].apply(lambda x: (x.iloc[-1]-x.iloc[0])/x.iloc[0]*100)
            monthly.index = [calendar.month_name[i] for i in monthly.index]
            st.bar_chart(monthly)
        else:
            st.error("Nessun dato trovato.")
    except:
        st.error("Errore nel caricamento del dettaglio.")

# --- MAIN ---
if st.session_state.page == 'dashboard':
    render_dashboard()
else:
    render_detail()
