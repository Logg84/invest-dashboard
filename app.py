import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Strategic Terminal v15.0", layout="wide")
st.markdown("""
<style>
    .stButton>button { width: 100%; padding: 0px; height: 2em; font-size: 0.8rem; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.2rem; }
    .sub-row { background-color: #f9f9f9; padding: 10px; border-radius: 5px; font-size: 0.9rem; border-left: 3px solid #ddd; }
    .header-style { font-weight: bold; opacity: 0.7; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# --- STATO NAVIGAZIONE ---
if 'expanded_id' not in st.session_state: st.session_state.expanded_id = None

# --- DATABASE COMPLETISSIMO (CON ISIN) ---
# Struttura: Proxy (per la classifica) + 3 ETF + 3 Azioni
db = {
    "GEO": {
        "USA (S&P 500)": {
            "p": "SPY",
            "etfs": [
                {"n": "Vanguard S&P 500", "t": "VOO", "isin": "US9229083632"},
                {"n": "Invesco QQQ (Nasdaq)", "t": "QQQ", "isin": "US46090E1038"},
                {"n": "iShares Russell 2000", "t": "IWM", "isin": "US4642876555"}
            ],
            "stocks": [
                {"n": "Microsoft", "t": "MSFT", "isin": "US5949181045"},
                {"n": "NVIDIA", "t": "NVDA", "isin": "US67066G1040"},
                {"n": "Apple", "t": "AAPL", "isin": "US0378331005"}
            ]
        },
        "India": {
            "p": "INDA",
            "etfs": [
                {"n": "iShares MSCI India", "t": "INDA", "isin": "US46429B5984"},
                {"n": "WisdomTree India Earn.", "t": "EPI", "isin": "US97717W4226"},
                {"n": "Franklin FTSE India", "t": "FLIN", "isin": "US3535162080"}
            ],
            "stocks": [
                {"n": "Reliance Ind. (GDR)", "t": "RIGD.IL", "isin": "US7594701077"},
                {"n": "Infosys (ADR)", "t": "INFY", "isin": "US4567881085"},
                {"n": "HDFC Bank (ADR)", "t": "HDB", "isin": "US40415F1012"}
            ]
        },
        "Cina": {
            "p": "FXI",
            "etfs": [
                {"n": "iShares China Large-Cap", "t": "FXI", "isin": "US4642871846"},
                {"n": "KraneShares CSI Internet", "t": "KWEB", "isin": "US5007673065"},
                {"n": "iShares MSCI China", "t": "MCHI", "isin": "US46429B6719"}
            ],
            "stocks": [
                {"n": "Alibaba Group", "t": "BABA", "isin": "US01609W1027"},
                {"n": "Tencent (OTC)", "t": "TCEHY", "isin": "US88032Q1094"},
                {"n": "PDD Holdings", "t": "PDD", "isin": "US7223041028"}
            ]
        },
        "Europa": {
            "p": "IEUR",
            "etfs": [
                {"n": "Vanguard FTSE Europe", "t": "VGK", "isin": "US9220428745"},
                {"n": "SPDR Euro Stoxx 50", "t": "FEZ", "isin": "US78463X2027"},
                {"n": "iShares MSCI Eurozone", "t": "EZU", "isin": "US4642874659"}
            ],
            "stocks": [
                {"n": "Novo Nordisk (ADR)", "t": "NVO", "isin": "US6701002056"},
                {"n": "ASML Holding", "t": "ASML", "isin": "USN070592100"},
                {"n": "LVMH (OTC)", "t": "LVMUY", "isin": "US5024413065"}
            ]
        },
        "Giappone": {
            "p": "EWJ",
            "etfs": [
                {"n": "iShares MSCI Japan", "t": "EWJ", "isin": "US4642866085"},
                {"n": "WisdomTree Japan Hedged", "t": "DXJ", "isin": "US97717W8516"},
                {"n": "Franklin FTSE Japan", "t": "FLJP", "isin": "US35473P6786"}
            ],
            "stocks": [
                {"n": "Toyota Motor", "t": "TM", "isin": "US8923313071"},
                {"n": "Sony Group", "t": "SONY", "isin": "US8356993076"},
                {"n": "Mitsubishi UFJ", "t": "MUFG", "isin": "US6068221048"}
            ]
        },
        "Italia": {
            "p": "EWI",
            "etfs": [
                {"n": "iShares MSCI Italy", "t": "EWI", "isin": "US4642867315"},
                {"n": "Franklin FTSE Italy", "t": "FLIY", "isin": "US35473P7446"},
                {"n": "Xtrackers MSCI Italy", "t": "XMIV.DE", "isin": "LU0514695856"}
            ],
            "stocks": [
                {"n": "Ferrari NV", "t": "RACE", "isin": "NL0011585146"},
                {"n": "Eni SpA (ADR)", "t": "E", "isin": "US26874Q1085"},
                {"n": "Stellantis", "t": "STLA", "isin": "NL00150001Q9"}
            ]
        },
    },
    "SECTOR": {
        "Technology": {
            "p": "XLK",
            "etfs": [{"n": "Tech Select Sector", "t": "XLK", "isin": "US81369Y8030"}, {"n": "Vanguard Info Tech", "t": "VGT", "isin": "US92204A7028"}, {"n": "Fidelity MSCI Tech", "t": "FTEC", "isin": "US3160922934"}],
            "stocks": [{"n": "Microsoft", "t": "MSFT", "isin": "US5949181045"}, {"n": "Apple", "t": "AAPL", "isin": "US0378331005"}, {"n": "NVIDIA", "t": "NVDA", "isin": "US67066G1040"}]
        },
        "Energy": {
            "p": "XLE",
            "etfs": [{"n": "Energy Select Sector", "t": "XLE", "isin": "US81369Y5069"}, {"n": "Vanguard Energy", "t": "VDE", "isin": "US92204A3068"}, {"n": "iShares Global Energy", "t": "IXC", "isin": "US4642873412"}],
            "stocks": [{"n": "Exxon Mobil", "t": "XOM", "isin": "US30231G1022"}, {"n": "Chevron", "t": "CVX", "isin": "US1667641005"}, {"n": "ConocoPhillips", "t": "COP", "isin": "US20825C1045"}]
        },
        "Healthcare": {
            "p": "XLV",
            "etfs": [{"n": "Health Care Select", "t": "XLV", "isin": "US81369Y2090"}, {"n": "Vanguard Health Care", "t": "VHT", "isin": "US92204A5048"}, {"n": "iShares Global Health", "t": "IXJ", "isin": "US4642873339"}],
            "stocks": [{"n": "Eli Lilly", "t": "LLY", "isin": "US5324571083"}, {"n": "UnitedHealth", "t": "UNH", "isin": "US91324P1021"}, {"n": "Johnson & Johnson", "t": "JNJ", "isin": "US4781601046"}]
        },
        "Gold Miners": {
            "p": "GDX",
            "etfs": [{"n": "VanEck Gold Miners", "t": "GDX", "isin": "US92189F1066"}, {"n": "VanEck Junior Miners", "t": "GDXJ", "isin": "US92189F7915"}, {"n": "iShares MSCI Global Gold", "t": "RING", "isin": "US46434V6130"}],
            "stocks": [{"n": "Newmont", "t": "NEM", "isin": "US6516391066"}, {"n": "Barrick Gold", "t": "GOLD", "isin": "CA0679011084"}, {"n": "Agnico Eagle", "t": "AEM", "isin": "CA0084741085"}]
        },
        "Defense": {
            "p": "ITA",
            "etfs": [{"n": "iShares US Aerospace", "t": "ITA", "isin": "US4642887602"}, {"n": "Invesco Aerospace", "t": "PPA", "isin": "US46137V1008"}, {"n": "SPDR Aerospace & Def", "t": "XAR", "isin": "US78464A6644"}],
            "stocks": [{"n": "RTX Corp", "t": "RTX", "isin": "US75513E1010"}, {"n": "Lockheed Martin", "t": "LMT", "isin": "US5398301094"}, {"n": "General Dynamics", "t": "GD", "isin": "US3695501086"}]
        },
        "Uranium": {
            "p": "URA",
            "etfs": [{"n": "Global X Uranium", "t": "URA", "isin": "US37954Y8710"}, {"n": "Sprott Uranium Miners", "t": "URNM", "isin": "US85208P3038"}, {"n": "VanEck Uranium", "t": "NLR", "isin": "US92189F6016"}],
            "stocks": [{"n": "Cameco", "t": "CCJ", "isin": "CA13321L1085"}, {"n": "NexGen Energy", "t": "NXE", "isin": "CA65340P1062"}, {"n": "Uranium Energy", "t": "UEC", "isin": "US9168961038"}]
        }
    },
    "PILLARS": {
        "1. DIFESA": {
            "p": "GLD",
            "alts": [
                {"n": "iShares Gold Trust", "t": "IAU", "isin": "US4642851053"},
                {"n": "iShares 1-3Y Treasury", "t": "SHY", "isin": "US4642874576"},
                {"n": "iShares Silver Trust", "t": "SLV", "isin": "US46428Q1094"}
            ]
        },
        "2. INFRA / AI": {
            "p": "COPX",
            "alts": [
                {"n": "Global X Uranium", "t": "URA", "isin": "US37954Y8710"},
                {"n": "US Infrastructure", "t": "PAVE", "isin": "US37950E3661"},
                {"n": "First Trust Smart Grid", "t": "GRID", "isin": "US33733E5092"}
            ]
        },
        "3. CICLICI": {
            "p": "IWM",
            "alts": [
                {"n": "Vanguard Value", "t": "VTV", "isin": "US9229087443"},
                {"n": "iShares Core Small-Cap", "t": "IJR", "isin": "US4642878049"},
                {"n": "iShares Emerging Mkts", "t": "EEM", "isin": "US4642872349"}
            ]
        },
        "4. SPECULATIVI": {
            "p": "BTC-USD",
            "alts": [
                {"n": "Ethereum USD", "t": "ETH-USD", "isin": "N/A"},
                {"n": "iShares Bitcoin Trust", "t": "IBIT", "isin": "US46438F1012"},
                {"n": "ProShares UltraPro QQQ", "t": "TQQQ", "isin": "US74347X8314"}
            ]
        }
    }
}

# --- ENGINE ---
def analyze_ticker(ticker):
    """Scarica dati 2 anni e calcola 1M, 3M, 6M, 1Y"""
    try:
        # Time.sleep per evitare blocchi se l'utente clicca veloce
        time.sleep(0.05)
        df = yf.download(ticker, period="2y", progress=False)
        
        if df.empty or len(df) < 50: return None
        
        # Gestione dataframe multi-livello
        try:
            closes = df['Close'].iloc[:, 0]
        except:
            closes = df['Close']
            
        curr = float(closes.iloc[-1])
        
        def get_px(d):
            idx = -d if len(closes) > d else 0
            return float(closes.iloc[idx])
            
        p1m, p3m, p6m, p1y = get_px(22), get_px(65), get_px(130), get_px(252)
        
        perf_1m = ((curr - p1m)/p1m)*100
        perf_3m = ((curr - p3m)/p3m)*100
        perf_6m = ((curr - p6m)/p6m)*100
        perf_1y = ((curr - p1y)/p1y)*100
        
        # Score severo (/3)
        w_perf = (perf_3m*0.4) + (perf_1m*0.3) + (perf_6m*0.2) + (perf_1y*0.1)
        score = max(min(w_perf / 3.0, 10), -10)
        
        return {
            "score": score,
            "p1m": perf_1m, "p3m": perf_3m, "p6m": perf_6m, "p1y": perf_1y,
            "price": curr
        }
    except:
        return None

# --- UI COMPONENTS ---
def color_val(val):
    c = "green" if val > 0 else "red"
    return f":{c}[{val:.1f}%]"

def render_main_header():
    c1, c2, c3, c4, c5, c6, c7 = st.columns([3, 1, 1, 1, 1, 1, 1])
    c1.markdown("**NOME ASSET**")
    c2.markdown("**SCORE**")
    c3.markdown("**1 M**")
    c4.markdown("**3 M**")
    c5.markdown("**6 M**")
    c6.markdown("**1 Y**")
    c7.markdown("**ACT**")
    st.divider()

def render_section(section_key, title):
    st.header(title)
    render_main_header()
    
    # Progresso iniziale per caricare la classifica
    items = list(db[section_key].items())
    results = []
    
    # Progress Bar solo per i Proxy (veloce)
    prog = st.progress(0)
    for i, (name, data) in enumerate(items):
        stats = analyze_ticker(data['p'])
        if stats:
            results.append({**stats, "name": name, "key": name, "data": data})
        prog.progress((i+1)/len(items))
    prog.empty()
    
    # Ordina
    results.sort(key=lambda x: x['score'], reverse=True)
    
    for row in results:
        c1, c2, c3, c4, c5, c6, c7 = st.columns([3, 1, 1, 1, 1, 1, 1])
        
        icon = "🔥" if row['score'] > 7 else ("❄️" if row['score'] < -7 else "➖")
        c1.markdown(f"**{icon} {row['name']}**")
        
        sc_col = "green" if row['score'] > 0 else "red"
        c2.markdown(f":{sc_col}[**{row['score']:.1f}**]")
        
        c3.markdown(color_val(row['p1m']))
        c4.markdown(color_val(row['p3m']))
        c5.markdown(color_val(row['p6m']))
        c6.markdown(color_val(row['p1y']))
        
        # Bottone Espansione
        is_expanded = (st.session_state.expanded_id == row['key'])
        label = "⬇️ Dettagli" if not is_expanded else "❌ Chiudi"
        
        if c7.button(label, key=f"btn_{row['key']}"):
            if is_expanded:
                st.session_state.expanded_id = None
            else:
                st.session_state.expanded_id = row['key']
            st.rerun()
            
        # SPACCATO (Caricato SOLO se espanso)
        if is_expanded:
            with st.container(border=True):
                st.markdown(f"#### 🔎 Analisi Approfondita: {row['name']}")
                
                # Combiniamo ETF e Stocks se ci sono
                sub_assets = []
                if 'etfs' in row['data']: sub_assets += row['data']['etfs']
                if 'stocks' in row['data']: sub_assets += row['data']['stocks']
                if 'alts' in row['data']: sub_assets += row['data']['alts'] # Per i pilastri
                
                # Header Sub-tabella
                sc1, sc2, sc3, sc4, sc5, sc6, sc7, sc8 = st.columns([2, 1, 2, 1, 1, 1, 1, 1])
                sc1.caption("NOME")
                sc2.caption("TICKER")
                sc3.caption("ISIN")
                sc4.caption("PREZZO")
                sc5.caption("1M")
                sc6.caption("6M")
                sc7.caption("1Y")
                sc8.caption("LINK")
                st.divider()
                
                # Caricamento Live dei Sottostanti
                with st.spinner(f"Scaricamento dati per {len(sub_assets)} asset..."):
                    for asset in sub_assets:
                        s_stats = analyze_ticker(asset['t'])
                        if s_stats:
                            sc1, sc2, sc3, sc4, sc5, sc6, sc7, sc8 = st.columns([2, 1, 2, 1, 1, 1, 1, 1])
                            sc1.write(f"**{asset['n']}**")
                            sc2.write(f"`{asset['t']}`")
                            sc3.write(f"{asset['isin']}")
                            sc4.write(f"${s_stats['price']:.2f}")
                            sc5.markdown(color_val(s_stats['p1m']))
                            sc6.markdown(color_val(s_stats['p6m']))
                            sc7.markdown(color_val(s_stats['p1y']))
                            sc8.link_button("🌐", f"https://finance.yahoo.com/quote/{asset['t']}")
                st.write("") # Spacer

# --- MAIN ---
st.title("🌍 Strategic Terminal v15.0")
st.caption("Dati Completi • Performance 1M/3M/6M/1Y • Spaccato ETF/Azioni con ISIN")

if st.button("🔄 AGGIORNA DATI"):
    st.cache_data.clear()
    st.rerun()

render_section("GEO", "1. 🗺️ CLASSIFICA NAZIONI")
st.markdown("---")
render_section("SECTOR", "2. 🏭 CLASSIFICA SETTORI")
st.markdown("---")
render_section("PILLARS", "3. 🏛️ I 4 PILASTRI STRATEGICI")
