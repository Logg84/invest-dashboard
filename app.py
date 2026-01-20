import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import calendar

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Strategic Terminal v5.0", layout="wide")

# --- STATO DELLA NAVIGAZIONE ---
if 'page' not in st.session_state: st.session_state.page = 'dashboard'
if 'selected_asset' not in st.session_state: st.session_state.selected_asset = None 
if 'expanded_geo' not in st.session_state: st.session_state.expanded_geo = None
if 'expanded_sector' not in st.session_state: st.session_state.expanded_sector = None

# --- DATABASE COMPLETO (EUROPA ESPLOSA & TUTTI I SETTORI) ---
db_structure = {
    "GEO": {
        "USA (S&P 500)": {
            "proxy": "SPY",
            "assets": [
                {"t": "VOO", "n": "Vanguard S&P 500", "type": "ETF"},
                {"t": "MSFT", "n": "Microsoft", "type": "Stock"},
                {"t": "NVDA", "n": "NVIDIA", "type": "Stock"}
            ]
        },
        "India": {
            "proxy": "INDA",
            "assets": [
                {"t": "INDA", "n": "iShares MSCI India", "type": "ETF"},
                {"t": "RIGD.IL", "n": "Reliance Ind. (GDR)", "type": "Stock"},
                {"t": "TTM", "n": "Tata Motors", "type": "Stock"}
            ]
        },
        "Germania": {
            "proxy": "EWG",
            "assets": [
                {"t": "EWG", "n": "iShares MSCI Germany", "type": "ETF"},
                {"t": "DAX", "n": "Global X DAX", "type": "ETF"},
                {"t": "SIE.DE", "n": "Siemens AG", "type": "Stock"},
                {"t": "SAP", "n": "SAP SE", "type": "Stock"}
            ]
        },
        "Regno Unito": {
            "proxy": "EWU",
            "assets": [
                {"t": "EWU", "n": "iShares MSCI UK", "type": "ETF"},
                {"t": "ISF.L", "n": "iShares FTSE 100", "type": "ETF"},
                {"t": "AZN", "n": "AstraZeneca", "type": "Stock"},
                {"t": "SHEL", "n": "Shell PLC", "type": "Stock"}
            ]
        },
        "Italia": {
            "proxy": "EWI",
            "assets": [
                {"t": "EWI", "n": "iShares MSCI Italy", "type": "ETF"},
                {"t": "ISP.MI", "n": "Intesa Sanpaolo", "type": "Stock"},
                {"t": "ENI.MI", "n": "Eni SpA", "type": "Stock"},
                {"t": "RACE", "n": "Ferrari", "type": "Stock"}
            ]
        },
        "Francia": {
            "proxy": "EWQ",
            "assets": [
                {"t": "EWQ", "n": "iShares MSCI France", "type": "ETF"},
                {"t": "MC.PA", "n": "LVMH", "type": "Stock"},
                {"t": "TTE", "n": "TotalEnergies", "type": "Stock"}
            ]
        },
        "Svizzera": {
            "proxy": "EWL",
            "assets": [
                {"t": "EWL", "n": "iShares MSCI Switzerland", "type": "ETF"},
                {"t": "NESN.SW", "n": "Nestlé", "type": "Stock"},
                {"t": "NOVN.SW", "n": "Novartis", "type": "Stock"}
            ]
        },
        "Cina": {
            "proxy": "FXI",
            "assets": [
                {"t": "FXI", "n": "China Large-Cap", "type": "ETF"},
                {"t": "BABA", "n": "Alibaba", "type": "Stock"},
                {"t": "PDD", "n": "PDD Holdings", "type": "Stock"}
            ]
        },
        "Giappone": {
            "proxy": "EWJ",
            "assets": [
                {"t": "EWJ", "n": "iShares MSCI Japan", "type": "ETF"},
                {"t": "TM", "n": "Toyota", "type": "Stock"},
                {"t": "SONY", "n": "Sony Group", "type": "Stock"}
            ]
        },
        "Brasile": {
            "proxy": "EWZ",
            "assets": [
                {"t": "EWZ", "n": "iShares MSCI Brazil", "type": "ETF"},
                {"t": "PBR", "n": "Petrobras", "type": "Stock"},
                {"t": "VALE", "n": "Vale SA", "type": "Stock"}
            ]
        }
    },
    "SECTOR": {
        "Technology": {"proxy": "XLK", "assets": [{"t": "XLK", "n": "Tech ETF", "type": "ETF"}, {"t": "NVDA", "n": "Nvidia", "type": "Stock"}]},
        "Energy": {"proxy": "XLE", "assets": [{"t": "XLE", "n": "Energy ETF", "type": "ETF"}, {"t": "XOM", "n": "Exxon", "type": "Stock"}]},
        "Financials": {"proxy": "XLF", "assets": [{"t": "XLF", "n": "Financial ETF", "type": "ETF"}, {"t": "JPM", "n": "JPMorgan", "type": "Stock"}]},
        "Healthcare": {"proxy": "XLV", "assets": [{"t": "XLV", "n": "Health ETF", "type": "ETF"}, {"t": "LLY", "n": "Eli Lilly", "type": "Stock"}]},
        "Cons. Discretionary": {"proxy": "XLY", "assets": [{"t": "XLY", "n": "Cons. Discr. ETF", "type": "ETF"}, {"t": "AMZN", "n": "Amazon", "type": "Stock"}]},
        "Industrials": {"proxy": "XLI", "assets": [{"t": "XLI", "n": "Industrial ETF", "type": "ETF"}, {"t": "CAT", "n": "Caterpillar", "type": "Stock"}]},
        "Utilities": {"proxy": "XLU", "assets": [{"t": "XLU", "n": "Utilities ETF", "type": "ETF"}, {"t": "NEE", "n": "NextEra", "type": "Stock"}]},
        "Materials": {"proxy": "XLB", "assets": [{"t": "XLB", "n": "Materials ETF", "type": "ETF"}, {"t": "LIN", "n": "Linde", "type": "Stock"}]},
        "Real Estate": {"proxy": "XLRE", "assets": [{"t": "XLRE", "n": "Real Estate ETF", "type": "ETF"}, {"t": "PLD", "n": "Prologis", "type": "Stock"}]},
        "Cons. Staples": {"proxy": "XLP", "assets": [{"t": "XLP", "n": "Staples ETF", "type": "ETF"}, {"t": "PG", "n": "Procter & Gamble", "type": "Stock"}]},
        "Comm. Services": {"proxy": "XLC", "assets": [{"t": "XLC", "n": "Comm. ETF", "type": "ETF"}, {"t": "GOOGL", "n": "Google", "type": "Stock"}]},
        "Gold Miners": {"proxy": "GDX", "assets": [{"t": "GDX", "n": "Gold Miners", "type": "ETF"}, {"t": "NEM", "n": "Newmont", "type": "Stock"}]},
        "Aerospace & Def": {"proxy": "ITA", "assets": [{"t": "ITA", "n": "Defense ETF", "type": "ETF"}, {"t": "LMT", "n": "Lockheed", "type": "Stock"}]},
    },
    "PILLARS": {
        "1. DIFESA / AIRBAG": {
            "main": {"t": "GLD", "n": "Oro Fisico"},
            "alts": [
                {"t": "SHY", "n": "Bond USA 1-3Y"},
                {"t": "SLV", "n": "Argento"}
            ]
        },
        "2. INFRA / REAL AI": {
            "main": {"t": "COPX", "n": "Rame Miners"},
            "alts": [
                {"t": "URA", "n": "Uranio"},
                {"t": "PAVE", "n": "Infrastrutture USA"}
            ]
        },
        "3. CICLICI / MOTORE": {
            "main": {"t": "IWM", "n": "Small Caps USA"},
            "alts": [
                {"t": "VTV", "n": "Value Stocks"},
                {"t": "EEM", "n": "Emerging Mkts"}
            ]
        },
        "4. SPECULATIVI": {
            "main": {"t": "BTC-USD", "n": "Bitcoin"},
            "alts": [
                {"t": "ETH-USD", "n": "Ethereum"},
                {"t": "QQQ", "n": "Nasdaq 100 (Leva 1)"}
            ]
        }
    }
}

# --- FUNZIONI CALCOLO ---
@st.cache_data(ttl=3600)
def get_extended_data(ticker):
    # Scarichiamo 2 anni di dati per calcolare tutto
    df = yf.download(ticker, period="2y", progress=False)
    if len(df) == 0: return None
    
    curr = float(df['Close'].iloc[-1])
    
    # Helper per trovare il prezzo N giorni fa
    def get_past_price(days):
        if len(df) > days: return float(df['Close'].iloc[-days])
        return float(df['Close'].iloc[0])

    p1m = get_past_price(22)  # ~1 mese di trading
    p3m = get_past_price(65)  # ~3 mesi
    p6m = get_past_price(130) # ~6 mesi
    p1y = get_past_price(252) # ~1 anno
    
    perf_1m = ((curr - p1m) / p1m) * 100
    perf_3m = ((curr - p3m) / p3m) * 100
    perf_6m = ((curr - p6m) / p6m) * 100
    perf_1y = ((curr - p1y) / p1y) * 100
    
    # Score Ponderato (-10/+10)
    # Diamo più peso al breve (3m) ma consideriamo il trend annuale
    raw_score = (perf_3m * 0.4) + (perf_1m * 0.3) + (perf_6m * 0.2) + (perf_1y * 0.1)
    score = max(min(raw_score, 10), -10)
    
    # Trend Semplice
    sma200 = df['Close'].rolling(200).mean().iloc[-1] if len(df) > 200 else p6m
    trend = "BULL" if curr > sma200 else "BEAR"
    
    return {
        "price": curr,
        "score": score,
        "trend": trend,
        "p1m": perf_1m,
        "p3m": perf_3m,
        "p6m": perf_6m,
        "p1y": perf_1y
    }

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

# --- PAGINA DASHBOARD ---
def render_dashboard():
    st.title("🌍 Global Strategy Terminal")
    st.markdown("Analisi Multi-Timeframe e Multi-Asset Class")

    # === SEZIONE 1: GEOGRAFIA (DETTAGLIATA) ===
    st.header("1. Analisi Geografica (Performance)")
    
    # Header Colonne
    c1, c2, c3, c4, c5, c6, c7 = st.columns([2.5, 1, 1, 1, 1, 1, 1])
    c1.markdown("**NAZIONE / AREA**")
    c2.markdown("**1 M**")
    c3.markdown("**3 M**")
    c4.markdown("**6 M**")
    c5.markdown("**1 A**")
    c6.markdown("**SCORE**")
    c7.markdown("**ACTION**")
    st.divider()

    # Calcolo Dati
    geo_list = []
    for area, data in db_structure['GEO'].items():
        stats = get_extended_data(data['proxy'])
        if stats:
            geo_list.append({**stats, "Area": area})
    
    # Ordinamento per Score
    df_geo = pd.DataFrame(geo_list).sort_values(by="score", ascending=False)

    for _, row in df_geo.iterrows():
        c1, c2, c3, c4, c5, c6, c7 = st.columns([2.5, 1, 1, 1, 1, 1, 1])
        
        c1.subheader(row['Area'])
        
        # Colora le performance
        def color_val(val):
            return f":green[{val:.1f}%]" if val > 0 else f":red[{val:.1f}%]"

        c2.markdown(color_val(row['p1m']))
        c3.markdown(color_val(row['p3m']))
        c4.markdown(color_val(row['p6m']))
        c5.markdown(color_val(row['p1y']))
        
        score_color = "green" if row['score'] > 0 else "red"
        c6.markdown(f":{score_color}[**{row['score']:.1f}**]")
        
        label = "⬇️" if st.session_state.expanded_geo == row['Area'] else "▶️"
        if c7.button(label, key=f"btn_geo_{row['Area']}"):
            toggle_geo(row['Area'])
            st.rerun()
            
        # SPACCATO GEO
        if st.session_state.expanded_geo == row['Area']:
            with st.container(border=True):
                st.info(f"Top Asset per: {row['Area']}")
                assets = db_structure['GEO'][row['Area']]['assets']
                ac1, ac2, ac3, ac4 = st.columns([3, 2, 2, 1])
                ac1.caption("NOME")
                ac2.caption("TIPO")
                ac3.caption("PREZZO")
                
                for asset in assets:
                    astats = get_extended_data(asset['t'])
                    if astats:
                        ac1, ac2, ac3, ac4 = st.columns([3, 2, 2, 1])
                        ac1.write(f"**{asset['n']}**")
                        ac2.write(asset['type'])
                        ac3.write(f"${astats['price']:.2f}")
                        if ac4.button("📊", key=f"d_g_{asset['t']}"):
                            show_detail(asset['t'])
                            st.rerun()
            st.divider()

    st.markdown("---")

    # === SEZIONE 2: SETTORI (SCROLLABLE & COMPLETA) ===
    st.header("2. Analisi Settoriale (Completa)")
    st.caption("Tutti i settori GICS ordinati per forza relativa.")
    
    # Header
    s1, s2, s3, s4 = st.columns([3, 1, 1, 1])
    s1.markdown("**SETTORE**")
    s2.markdown("**SCORE**")
    s3.markdown("**1 MESE**")
    s4.markdown("**DETTAGLI**")
    st.divider()
    
    sect_list = []
    for sect, data in db_structure['SECTOR'].items():
        stats = get_extended_data(data['proxy'])
        if stats:
            sect_list.append({**stats, "Settore": sect})
            
    df_sect = pd.DataFrame(sect_list).sort_values(by="score", ascending=False)
    
    # Scrollable container simulato (Streamlit lo gestisce nativamente se la pagina è lunga)
    for _, row in df_sect.iterrows():
        s1, s2, s3, s4 = st.columns([3, 1, 1, 1])
        s1.write(f"**{row['Settore']}**")
        
        sc_color = "green" if row['score'] > 0 else "red"
        s2.markdown(f":{sc_color}[{row['score']:.1f}]")
        
        p_color = "green" if row['p1m'] > 0 else "red"
        s3.markdown(f":{p_color}[{row['p1m']:.1f}%]")
        
        lab = "⬇️" if st.session_state.expanded_sector == row['Settore'] else "▶️"
        if s4.button(lab, key=f"btn_sec_{row['Settore']}"):
            toggle_sector(row['Settore'])
            st.rerun()
            
        if st.session_state.expanded_sector == row['Settore']:
            with st.container(border=True):
                assets = db_structure['SECTOR'][row['Settore']]['assets']
                for asset in assets:
                    astats = get_extended_data(asset['t'])
                    if astats:
                        c_a, c_b, c_c = st.columns([4, 2, 1])
                        c_a.write(f"{asset['n']} ({asset['t']})")
                        c_b.write(f"${astats['price']:.2f}")
                        if c_c.button("📊", key=f"d_s_{asset['t']}"):
                            show_detail(asset['t'])
                            st.rerun()
            st.divider()

    st.markdown("---")

    # === SEZIONE 3: I 4 PILASTRI (CON ALTERNATIVE) ===
    st.header("3. I 4 Pilastri & Alternative")
    
    cols = st.columns(4)
    i = 0
    for pillar_name, data in db_structure['PILLARS'].items():
        with cols[i]:
            with st.container(border=True):
                st.subheader(pillar_name)
                
                # Main Asset
                main = data['main']
                m_stats = get_extended_data(main['t'])
                
                if m_stats:
                    st.markdown(f"**👑 Main: {main['n']}**")
                    col_m1, col_m2 = st.columns(2)
                    col_m1.metric("Prezzo", f"{m_stats['price']:.0f}")
                    col_m2.metric("Trend", m_stats['trend'], f"{m_stats['p1m']:.1f}%")
                    
                    if m_stats['trend'] == "BULL":
                        st.success("BULLISH")
                    else:
                        st.error("BEARISH")
                
                st.divider()
                st.markdown("**🔄 Alternative:**")
                
                for alt in data['alts']:
                    a_stats = get_extended_data(alt['t'])
                    if a_stats:
                        icon = "🟢" if a_stats['trend'] == "BULL" else "🔴"
                        st.write(f"{icon} **{alt['n']}**: {a_stats['p1m']:.1f}% (1M)")
                        if st.button(f"Analizza {alt['t']}", key=f"alt_{alt['t']}"):
                            show_detail(alt['t'])
                            st.rerun()
        i += 1

# --- PAGINA DETTAGLIO ---
def render_detail():
    tk = st.session_state.selected_asset
    st.button("🔙 TORNA ALLA DASHBOARD", on_click=back_to_dash)
    st.title(f"Analisi Approfondita: {tk}")
    
    df = yf.download(tk, period="2y", progress=False)
    if len(df) > 0:
        # Grafico
        st.subheader("Prezzo & Medie Mobili")
        df['SMA50'] = df['Close'].rolling(50).mean()
        df['SMA200'] = df['Close'].rolling(200).mean()
        st.line_chart(df[['Close', 'SMA50', 'SMA200']])
        
        # Statistiche
        st.subheader("Statistiche Chiave")
        curr = df['Close'].iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Prezzo", f"${curr:.2f}")
        c2.metric("Volatilità (Annuale)", f"{df['Close'].pct_change().std()*np.sqrt(252)*100:.1f}%")
        
        # Stagionalità
        st.subheader("📅 Stagionalità")
        df['M'] = df.index.month
        monthly = df.groupby('M')['Close'].apply(lambda x: (x.iloc[-1]-x.iloc[0])/x.iloc[0]*100)
        monthly.index = [calendar.month_name[i] for i in monthly.index]
        st.bar_chart(monthly)

# --- MAIN ---
if st.session_state.page == 'dashboard':
    render_dashboard()
else:
    render_detail()
