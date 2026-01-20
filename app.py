import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import calendar

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Strategic Terminal v3.0", layout="wide", initial_sidebar_state="collapsed")

# --- GESTIONE STATO (NAVIGAZIONE) ---
if 'page' not in st.session_state:
    st.session_state.page = 'main'
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None
if 'selected_isin' not in st.session_state:
    st.session_state.selected_isin = ""

# --- DATABASE ESTESO (5+ Opzioni) ---
assets_db = {
    "GEO": {
        "Emerging Markets": {
            "desc": "Mercati ad alta crescita (Cina, India, Brasile, Taiwan).",
            "etf": [
                {"name": "iShares Core MSCI EM IMI", "ticker": "EEM", "isin": "IE00BKM4GZ66"},
                {"name": "Vanguard FTSE Emerging Markets", "ticker": "VWO", "isin": "IE00BK5BR733"},
                {"name": "Xtrackers MSCI Emerging Markets", "ticker": "XMMS", "isin": "IE00BTJRMP35"},
                {"name": "Amundi MSCI Emerging Markets", "ticker": "AEEM", "isin": "LU1681045370"}
            ],
            "azioni": [
                {"name": "TSMC (Taiwan Semi)", "ticker": "TSM", "isin": "US8740391003"},
                {"name": "Tencent Holdings", "ticker": "TCEHY", "isin": "US88032Q1094"},
                {"name": "HDFC Bank (India)", "ticker": "HDB", "isin": "US40415F1012"},
                {"name": "Petrobras (Brasile)", "ticker": "PBR", "isin": "US71654V4086"},
                {"name": "Infosys", "ticker": "INFY", "isin": "US4567881085"}
            ]
        },
        "India": {
            "desc": "Focus sull'economia indiana (Demografia + Tech).",
            "etf": [
                {"name": "iShares MSCI India", "ticker": "INDA", "isin": "IE00BZCQB185"},
                {"name": "Franklin FTSE India", "ticker": "FLIN", "isin": "IE00BHZRQZ17"},
                {"name": "WisdomTree India Quality", "ticker": "EPI", "isin": "IE00BDGSNK96"}
            ],
            "azioni": [
                {"name": "Reliance Industries (GDR)", "ticker": "RIGD.IL", "isin": "US7594701077"},
                {"name": "Tata Motors", "ticker": "TTM", "isin": "US8765685024"},
                {"name": "ICICI Bank", "ticker": "IBN", "isin": "US45112F1012"},
                {"name": "Dr. Reddy's Lab", "ticker": "RDY", "isin": "US2561352038"}
            ]
        },
        "USA (S&P 500)": {
            "desc": "Mercato Americano Large Cap.",
            "etf": [
                {"name": "Vanguard S&P 500", "ticker": "VOO", "isin": "IE00B3XXRP09"},
                {"name": "iShares Core S&P 500", "ticker": "IVV", "isin": "IE00B5BMR087"},
                {"name": "Invesco S&P 500 Equal Weight", "ticker": "RSP", "isin": "IE00BNGJJT35"}
            ],
            "azioni": [
                {"name": "Microsoft", "ticker": "MSFT", "isin": "US5949181045"},
                {"name": "Apple", "ticker": "AAPL", "isin": "US0378331005"},
                {"name": "Amazon", "ticker": "AMZN", "isin": "US0231351067"},
                {"name": "Berkshire Hathaway", "ticker": "BRK-B", "isin": "US0846707026"},
                {"name": "JPMorgan Chase", "ticker": "JPM", "isin": "US46625H1005"}
            ]
        }
    },
    "SECTOR": {
        "Technology": {
            "desc": "Software, Hardware, AI, Semiconduttori.",
            "etf": [
                {"name": "iShares S&P 500 Info Tech", "ticker": "XLK", "isin": "IE00B3WJKG14"},
                {"name": "VanEck Semiconductor", "ticker": "SMH", "isin": "IE00BMC38736"},
                {"name": "Xtrackers AI & Big Data", "ticker": "XAIX.DE", "isin": "IE00BGV5VN51"},
                {"name": "WisdomTree Cloud Computing", "ticker": "WCLD", "isin": "IE00BJGWQN72"}
            ],
            "azioni": [
                {"name": "NVIDIA", "ticker": "NVDA", "isin": "US67066G1040"},
                {"name": "Broadcom", "ticker": "AVGO", "isin": "US11135F1012"},
                {"name": "Oracle", "ticker": "ORCL", "isin": "US68389X1054"},
                {"name": "Salesforce", "ticker": "CRM", "isin": "US79466L3024"},
                {"name": "AMD", "ticker": "AMD", "isin": "US0079031078"}
            ]
        },
        "Energy & Uranium": {
            "desc": "Petrolio, Gas e Nucleare.",
            "etf": [
                {"name": "Xtrackers MSCI World Energy", "ticker": "XLE", "isin": "IE00BM67HM91"},
                {"name": "Global X Uranium", "ticker": "URA", "isin": "IE000NDWFGA5"},
                {"name": "Sprott Uranium Miners", "ticker": "URNM", "isin": "IE0005YK6564"},
                {"name": "iShares Oil & Gas Expl", "ticker": "IEO", "isin": "IE00B6R52036"}
            ],
            "azioni": [
                {"name": "Exxon Mobil", "ticker": "XOM", "isin": "US30231G1022"},
                {"name": "Chevron", "ticker": "CVX", "isin": "US1667641005"},
                {"name": "Cameco (Uranio)", "ticker": "CCJ", "isin": "CA13321L1085"},
                {"name": "Schlumberger", "ticker": "SLB", "isin": "AN8068571086"},
                {"name": "Occidental Petroleum", "ticker": "OXY", "isin": "US6745991058"}
            ]
        },
        "Aerospace & Defense": {
            "desc": "Difesa, Cyberwarfare e Aerospazio.",
            "etf": [
                {"name": "iShares US Aerospace & Def", "ticker": "ITA", "isin": "IE00B945C952 (Simile)"},
                {"name": "VanEck Defense UCITS", "ticker": "DFNS.L", "isin": "IE000YYE6WK5"},
                {"name": "HANetf Future of Defence", "ticker": "NATO.L", "isin": "IE000OJ5TQP4"}
            ],
            "azioni": [
                {"name": "Rheinmetall", "ticker": "RHM.DE", "isin": "DE0007030009"},
                {"name": "Leonardo", "ticker": "LDO.MI", "isin": "IT0003856405"},
                {"name": "Lockheed Martin", "ticker": "LMT", "isin": "US5398301094"},
                {"name": "RTX Corp", "ticker": "RTX", "isin": "US75513E1010"},
                {"name": "Palantir (Cyber/AI)", "ticker": "PLTR", "isin": "US69608A1088"}
            ]
        }
    },
    "FUTURE": {
        "Cybersecurity": {
            "ticker": "CIBR", 
            "isin": "IE00BYPLS672",
            "desc": "Con l'IA aumentano gli attacchi informatici. Settore strutturalmente in crescita."
        },
        "Clean Energy Grid": {
            "ticker": "ICLN",
            "isin": "IE00B1XNHC34",
            "desc": "L'AI ha bisogno di elettricità. Focus non sui pannelli, ma sulla rete e storage."
        },
        "Robotics & Automation": {
            "ticker": "ROBO",
            "isin": "IE00BMW3QX54",
            "desc": "Automazione industriale per il reshoring delle fabbriche in occidente."
        }
    }
}

# --- FUNZIONI DI NAVIGAZIONE ---
def go_to_detail(ticker, isin):
    st.session_state.selected_ticker = ticker
    st.session_state.selected_isin = isin
    st.session_state.page = 'detail'

def go_to_main():
    st.session_state.page = 'main'

# --- FUNZIONE ANALISI DETTAGLIO (MOTORE) ---
def render_detail_view():
    ticker_symbol = st.session_state.selected_ticker
    isin = st.session_state.selected_isin
    
    # Pulsante Indietro
    st.button("🔙 Torna alla Dashboard", on_click=go_to_main)
    
    st.title(f"Analisi Approfondita: {ticker_symbol}")
    st.caption(f"ISIN Riferimento: {isin}")
    
    # Scarico dati avanzati
    with st.spinner('Analisi dati in corso (Volumi, Stagionalità, Fondamentali)...'):
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="2y")
        info = stock.info
    
    if df.empty:
        st.error("Dati non disponibili per questo ticker.")
        return

    # 1. HEADER METRICHE
    col1, col2, col3, col4 = st.columns(4)
    current_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2]
    delta = ((current_price - prev_price)/prev_price)*100
    
    col1.metric("Prezzo", f"${current_price:.2f}", f"{delta:.2f}%")
    col2.metric("P/E Ratio", info.get('trailingPE', 'N/A'))
    col3.metric("Beta (Rischio)", info.get('beta', 'N/A'))
    col4.metric("52 Week High", info.get('fiftyTwoWeekHigh', 'N/A'))

    # 2. GRAFICO INTERATTIVO (Prezzo + Volumi)
    st.subheader("📈 Analisi Tecnica e Volumetrica")
    
    # Calcolo Medie Mobili
    df['SMA50'] = df['Close'].rolling(50).mean()
    df['SMA200'] = df['Close'].rolling(200).mean()
    
    chart_data = df[['Close', 'SMA50', 'SMA200']]
    st.line_chart(chart_data, color=["#ffffff", "#00ff00", "#ff0000"])
    
    # Analisi Volumi
    avg_vol = df['Volume'].mean()
    curr_vol = df['Volume'].iloc[-1]
    vol_status = "Alto (Interesse in crescita)" if curr_vol > avg_vol else "Basso (Interesse scarso)"
    st.info(f"📊 **Analisi Volumi:** Il volume di oggi è {curr_vol/1000000:.1f}M (Media: {avg_vol/1000000:.1f}M). Stato: **{vol_status}**")

    # 3. TABELLA FONDAMENTALI & DESCRIZIONE
    st.subheader("🏢 Profilo Aziendale / Asset")
    tab1, tab2, tab3 = st.tabs(["Descrizione", "Dati Finanziari", "Stagionalità"])
    
    with tab1:
        st.write(info.get('longBusinessSummary', "Descrizione non disponibile."))
        st.write(f"**Settore:** {info.get('sector', 'N/A')} | **Industria:** {info.get('industry', 'N/A')}")
    
    with tab2:
        c1, c2 = st.columns(2)
        c1.metric("Fatturato (Revenue)", f"${info.get('totalRevenue', 0)/1000000000:.2f} mld")
        c1.metric("Utile Netto", f"${info.get('netIncomeToCommon', 0)/1000000000:.2f} mld")
        c2.metric("Profit Margin", f"{info.get('profitMargins', 0)*100:.2f}%")
        c2.metric("Dividend Yield", f"{info.get('dividendRate', 0)*100:.2f}%" if info.get('dividendRate') else "N/A")
    
    with tab3:
        st.write("📅 **Analisi Stagionale (Ultimi 2 anni)**")
        st.caption("Quali sono i mesi migliori per questo asset?")
        
        # Calcolo stagionalità
        df_season = df.copy()
        df_season['Month'] = df_season.index.month
        monthly_avg = df_season.groupby('Month')['Close'].apply(lambda x: (x.iloc[-1] - x.iloc[0])/x.iloc[0] * 100)
        monthly_avg.index = [calendar.month_name[i] for i in monthly_avg.index]
        
        st.bar_chart(monthly_avg)
        st.caption("Barre in alto = Mese storicamente positivo. Barre in basso = Mese negativo.")

    # 4. PREVISIONE ALGORITMICA (Simulazione)
    st.markdown("---")
    st.subheader("🔮 Previsione Algoritmica (Medio Termine)")
    
    # Logica semplice
    trend = "RIALSISTA" if current_price > df['SMA200'].iloc[-1] else "RIBASSISTA"
    momentum = "POSITIVO" if current_price > df['SMA50'].iloc[-1] else "DEBOLE"
    
    forecast_col, reason_col = st.columns([1, 2])
    
    with forecast_col:
        if trend == "RIALSISTA" and momentum == "POSITIVO":
            st.success("## 🚀 BULLISH")
        elif trend == "RIBASSISTA" and momentum == "DEBOLE":
            st.error("## 🐻 BEARISH")
        else:
            st.warning("## ⚖️ NEUTRALE")
            
    with reason_col:
        st.write(f"**Analisi:** Il prezzo è sopra la media a 200 giorni ({trend}) e il momentum a breve termine è {momentum}.")
        st.write("**Strategia suggerita:** " + ("Buy the dip (compra sui ritracciamenti)" if trend == "RIALSISTA" else "Attendi inversione o stai liquido."))

# --- FUNZIONE MAIN DASHBOARD ---
def render_main_dashboard():
    st.title("🌍 Strategic Investment Terminal v3.0")
    st.markdown("Monitoraggio mercati, selezione asset e analisi approfondita.")

    # 1. ANALISI GEOGRAFICA
    st.header("1. 🗺️ Analisi Geografica (Top Picks)")
    geo_tabs = st.tabs(list(assets_db['GEO'].keys()))
    
    for i, region in enumerate(assets_db['GEO']):
        with geo_tabs[i]:
            data = assets_db['GEO'][region]
            st.caption(data['desc'])
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🛡️ ETF Consigliati")
                for etf in data['etf']:
                    with st.expander(f"📌 {etf['name']}"):
                        st.write(f"**ISIN:** `{etf['isin']}`")
                        # Bottone univoco
                        st.button(f"📊 Analizza {etf['ticker']}", key=f"btn_etf_{etf['ticker']}", on_click=go_to_detail, args=(etf['ticker'], etf['isin']))
            
            with c2:
                st.subheader("🚀 Azioni Top")
                for stk in data['azioni']:
                    with st.expander(f"🏢 {stk['name']}"):
                        st.write(f"**ISIN:** `{stk['isin']}`")
                        st.button(f"📊 Analizza {stk['ticker']}", key=f"btn_stk_{stk['ticker']}", on_click=go_to_detail, args=(stk['ticker'], stk['isin']))

    st.markdown("---")

    # 2. ANALISI SETTORIALE
    st.header("2. 🏭 Analisi Settoriale")
    sect_tabs = st.tabs(list(assets_db['SECTOR'].keys()))
    
    for i, sector in enumerate(assets_db['SECTOR']):
        with sect_tabs[i]:
            data = assets_db['SECTOR'][sector]
            st.caption(data['desc'])
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🛡️ ETF Settoriali")
                for etf in data['etf']:
                    with st.expander(f"📌 {etf['name']}"):
                        st.write(f"**ISIN:** `{etf['isin']}`")
                        st.button(f"📊 Analizza {etf['ticker']}", key=f"btn_sec_etf_{etf['ticker']}", on_click=go_to_detail, args=(etf['ticker'], etf['isin']))
            
            with c2:
                st.subheader("🚀 Azioni Leader")
                for stk in data['azioni']:
                    with st.expander(f"🏢 {stk['name']}"):
                        st.write(f"**ISIN:** `{stk['isin']}`")
                        st.button(f"📊 Analizza {stk['ticker']}", key=f"btn_sec_stk_{stk['ticker']}", on_click=go_to_detail, args=(stk['ticker'], stk['isin']))

    st.markdown("---")

    # 3. RADAR & SUGGERIMENTI
    st.header("3. 🔮 Radar: Trend Emergenti")
    st.info("Settori da monitorare per il prossimo ciclo (Watchlist).")
    
    cols = st.columns(3)
    for idx, (name, data) in enumerate(assets_db['FUTURE'].items()):
        with cols[idx]:
            with st.container(border=True):
                st.subheader(name)
                st.write(data['desc'])
                st.code(f"Ticker: {data['ticker']}\nISIN: {data['isin']}")
                st.button(f"🔎 Studia {name}", key=f"btn_fut_{data['ticker']}", on_click=go_to_detail, args=(data['ticker'], data['isin']))

# --- ROUTER (DECIDE COSA MOSTRARE) ---
if st.session_state.page == 'main':
    render_main_dashboard()
elif st.session_state.page == 'detail':
    render_detail_view()
