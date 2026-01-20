import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Strategic Investment Terminal", layout="wide")
st.title("🌍 Strategic Investment Terminal v2.0")
st.markdown("Sistema di Analisi Tattica con selezione strumenti (ISIN)")

# --- DATABASE STRUMENTI (ISIN & DETTAGLI) ---
# Qui colleghiamo l'indice generale agli strumenti reali acquistabili (ETF UCITS / Azioni)
drill_down_db = {
    # GEOGRAFICI
    "Emerging Markets": {
        "desc": "Mercati in via di sviluppo (Cina, India, Brasile). Alto rischio, alto potenziale.",
        "etf": [
            {"nome": "iShares Core MSCI EM IMI (Acc)", "isin": "IE00BKM4GZ66", "tipo": "ETF Azionario"},
            {"nome": "Vanguard FTSE Emerging Markets", "isin": "IE00BK5BR733", "tipo": "ETF Azionario"}
        ],
        "azioni": [
            {"nome": "TSMC (Semiconductors)", "ticker": "TSM", "isin": "US8740391003"},
            {"nome": "Tencent Holdings", "ticker": "TCEHY", "isin": "US88032Q1094"}
        ]
    },
    "India": {
        "desc": "L'economia a più forte crescita. Demografia giovane e digitalizzazione.",
        "etf": [
            {"nome": "iShares MSCI India UCITS ETF", "isin": "IE00BZCQB185", "tipo": "ETF Paese"},
            {"nome": "Franklin FTSE India", "isin": "IE00BHZRQZ17", "tipo": "ETF Paese (Low Cost)"}
        ],
        "azioni": [{"nome": "Reliance Industries (GDR)", "ticker": "RIGD", "isin": "US7594701077"}]
    },
    "Cina Large Cap": {
        "desc": "Le grandi aziende cinesi. Molto volatili, dipendono dalla politica governativa.",
        "etf": [{"nome": "Xtrackers MSCI China UCITS ETF", "isin": "LU0514695690", "tipo": "ETF Paese"}],
        "azioni": [{"nome": "Alibaba Group", "ticker": "BABA", "isin": "US01609W1027"}]
    },
    "Europa (Euro Stoxx 50)": {
        "desc": "Le 50 blue chips dell'area Euro.",
        "etf": [{"nome": "iShares Core EURO STOXX 50", "isin": "IE00B53L3W79", "tipo": "ETF Indice"}],
        "azioni": [{"nome": "ASML Holding", "ticker": "ASML", "isin": "NL0010273215"}]
    },
    "USA (S&P 500)": {
        "desc": "Il mercato principale globale.",
        "etf": [{"nome": "Vanguard S&P 500 UCITS ETF", "isin": "IE00B3XXRP09", "tipo": "ETF Indice"}],
        "azioni": [{"nome": "Microsoft", "ticker": "MSFT", "isin": "US5949181045"}]
    },
     "Giappone": {
        "desc": "Mercato stabile con focus su robotica e auto, beneficia di yen debole.",
        "etf": [{"nome": "Vanguard FTSE Japan", "isin": "IE00B95PGT31", "tipo": "ETF Indice"}],
        "azioni": [{"nome": "Toyota Motor", "ticker": "TM", "isin": "JP3633400001"}]
    },

    # SETTORIALI
    "Gold Miners": {
        "desc": "ATTENZIONE: Investire nei minatori è diverso dall'Oro fisico. I minatori hanno 'leva operativa' (salgono di più se l'oro sale, crollano se l'oro scende o se i costi energetici salgono).",
        "etf": [
            {"nome": "VanEck Gold Miners UCITS ETF", "isin": "IE00BQQP9F84", "tipo": "ETF Minatori (Volatile)"},
            {"nome": "Invesco Physical Gold (ETC)", "isin": "IE00B579F325", "tipo": "Alternative: Oro Fisico (Sicuro)"}
        ],
        "azioni": [
            {"nome": "Newmont Corp", "ticker": "NEM", "isin": "US6516391066"},
            {"nome": "Barrick Gold", "ticker": "GOLD", "isin": "CA0679011084"}
        ]
    },
    "Aerospace & Defense": {
        "desc": "Settore geopolitico. Beneficia dell'aumento della spesa militare globale.",
        "etf": [
            {"nome": "VanEck Defense UCITS ETF", "isin": "IE000YYE6WK5", "tipo": "ETF Settoriale"},
            {"nome": "HANetf Future of Defence", "isin": "IE000OJ5TQP4", "tipo": "ETF Tematico"}
        ],
        "azioni": [
            {"nome": "Leonardo SpA", "ticker": "LDO.MI", "isin": "IT0003856405"},
            {"nome": "Rheinmetall", "ticker": "RHM.DE", "isin": "DE0007030009"}
        ]
    },
    "Uranio (Nucleare)": {
        "desc": "Combustibile per l'IA e transizione energetica.",
        "etf": [{"nome": "Global X Uranium UCITS ETF", "isin": "IE000NDWFGA5", "tipo": "ETF Tematico"}],
        "azioni": [{"nome": "Cameco Corp", "ticker": "CCJ", "isin": "CA13321L1085"}]
    },
    "Technology": {
        "desc": "Software e Hardware. Alta crescita.",
        "etf": [{"nome": "iShares S&P 500 Info Tech", "isin": "IE00B3WJKG14", "tipo": "ETF Settoriale"}],
        "azioni": [{"nome": "NVIDIA", "ticker": "NVDA", "isin": "US67066G1040"}]
    },
    "Energy": {
        "desc": "Petrolio e Gas (Old Economy).",
        "etf": [{"nome": "Xtrackers MSCI World Energy", "isin": "IE00BM67HM91", "tipo": "ETF Settoriale"}],
        "azioni": [{"nome": "Exxon Mobil", "ticker": "XOM", "isin": "US30231G1022"}]
    }
}

# --- ASSET PER L'ANALISI MACRO ---
assets_analysis = {
    "GEO": [
        {"ticker": "EEM", "name": "Emerging Markets"},
        {"ticker": "INDA", "name": "India"},
        {"ticker": "FXI", "name": "Cina Large Cap"},
        {"ticker": "FEZ", "name": "Europa (Euro Stoxx 50)"},
        {"ticker": "SPY", "name": "USA (S&P 500)"},
        {"ticker": "EWJ", "name": "Giappone"}
    ],
    "SECTOR": [
        {"ticker": "GDX", "name": "Gold Miners"},
        {"ticker": "ITA", "name": "Aerospace & Defense"},
        {"ticker": "URA", "name": "Uranio (Nucleare)"},
        {"ticker": "XLK", "name": "Technology"},
        {"ticker": "XLE", "name": "Energy"},
        {"ticker": "XLV", "name": "Healthcare"}
    ],
    "PILLARS": [
        {"ticker": "GLD", "name": "Pilastro 1: ORO (Difesa)", "desc": "Protezione da inflazione e crisi."},
        {"ticker": "COPX", "name": "Pilastro 2: RAME (Infra)", "desc": "Materiale essenziale per l'IA."},
        {"ticker": "IWM", "name": "Pilastro 3: SMALL CAP (Ciclico)", "desc": "Motore dell'economia reale USA."},
        {"ticker": "BTC-USD", "name": "Pilastro 4: BITCOIN (Risk)", "desc": "Termometro della liquidità."}
    ]
}

# --- FUNZIONI DI CALCOLO ---
@st.cache_data(ttl=3600)
def analyze_data(asset_list):
    results = []
    for asset in asset_list:
        df = yf.download(asset['ticker'], period="6mo", progress=False)
        if len(df) > 0:
            curr = float(df['Close'].iloc[-1])
            start_3m = float(df['Close'].iloc[-65]) if len(df) > 65 else float(df['Close'].iloc[0])
            start_1m = float(df['Close'].iloc[-22]) if len(df) > 22 else float(df['Close'].iloc[0])
            
            perf_3m = ((curr - start_3m) / start_3m) * 100
            perf_1m = ((curr - start_1m) / start_1m) * 100
            
            # Punteggio Forza: Normalizzato tra -10 e +10 circa
            # Un mix di breve e medio termine
            score = (perf_3m * 0.6) + (perf_1m * 0.4)
            # Limitiamo visivamente a +/- 10 per leggibilità
            score_display = max(min(score, 10), -10)

            # SMA 200 per trend lungo
            sma200 = df['Close'].rolling(200).mean().iloc[-1] if len(df) > 199 else start_3m
            trend = "RIALSISTA" if curr > sma200 else "RIBASSISTA"

            results.append({
                "Nome Asset": asset['name'],
                "Simbolo": asset['ticker'], # Spiegazione: Codice univoco di borsa
                "Prezzo ($)": round(curr, 2),
                "Perf. 1 Mese": f"{perf_1m:+.2f}%",
                "Perf. 3 Mesi": f"{perf_3m:+.2f}%",
                "Forza (-10/+10)": round(score_display, 1),
                "Trend Lungo": trend,
                "_raw_score": score # Nascosto, serve per ordinare
            })
    return pd.DataFrame(results).sort_values(by="_raw_score", ascending=False)

# --- LAYOUT DASHBOARD ---

# 1. SEZIONE GEOGRAFICA
st.header("1. 🗺️ Analisi Geografica: Dove investire?")
st.info("La colonna 'Forza' indica il Momentum: più è alta (vicino a +10), più quel mercato sta attirando capitali oggi.")
df_geo = analyze_data(assets_analysis['GEO'])
st.dataframe(
    df_geo.drop(columns=["_raw_score"]).style.background_gradient(subset=['Forza (-10/+10)'], cmap='RdYlGn', vmin=-10, vmax=10),
    use_container_width=True,
    hide_index=True
)

# Drill-down Interattivo
selected_geo = st.selectbox("🔍 Seleziona un mercato per vedere gli STRUMENTI MIGLIORI (ETF/Azioni):", df_geo['Nome Asset'].tolist())

if selected_geo in drill_down_db:
    details = drill_down_db[selected_geo]
    st.markdown(f"**Analisi per: {selected_geo}**")
    st.caption(details['desc'])
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🛡️ ETF Consigliati (ISIN)")
        for etf in details['etf']:
            st.success(f"**{etf['nome']}**\n\nISIN: `{etf['isin']}`\n\nTipo: *{etf['tipo']}*")
    with col_b:
        st.subheader("🚀 Azioni Top Picks")
        if 'azioni' in details:
            for stk in details['azioni']:
                st.warning(f"**{stk['nome']}** ({stk['ticker']})\n\nISIN: `{stk['isin']}`")
        else:
            st.write("Nessuna azione singola consigliata, meglio usare ETF.")
else:
    st.write("Dettagli specifici non disponibili per questo indice generico.")

st.markdown("---")

# 2. SEZIONE SETTORIALE
st.header("2. 🏭 Analisi Settoriale: In cosa investire?")
df_sector = analyze_data(assets_analysis['SECTOR'])
st.dataframe(
    df_sector.drop(columns=["_raw_score"]).style.background_gradient(subset=['Forza (-10/+10)'], cmap='RdYlGn', vmin=-10, vmax=10),
    use_container_width=True,
    hide_index=True
)

# Drill-down Settoriale
selected_sect = st.selectbox("🔍 Seleziona un settore per vedere gli ISIN:", df_sector['Nome Asset'].tolist())

if selected_sect in drill_down_db:
    details = drill_down_db[selected_sect]
    st.markdown(f"**Focus Settore: {selected_sect}**")
    st.caption(details['desc'])
    
    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("🛡️ ETF / ETC")
        for etf in details['etf']:
            st.success(f"**{etf['nome']}**\n\nISIN: `{etf['isin']}`\n\nTipo: *{etf['tipo']}*")
    with col_d:
        st.subheader("🚀 Azioni Leader")
        for stk in details['azioni']:
            st.warning(f"**{stk['nome']}** ({stk['ticker']})\n\nISIN: `{stk['isin']}`")

st.markdown("---")

# 3. I 4 PILASTRI
st.header("3. 🏛️ Stato della Strategia (4 Pilastri)")
st.markdown("Questa sezione ti dice come bilanciare il portafoglio in base al contesto.")

df_pillars = analyze_data(assets_analysis['PILLARS'])

# Creiamo delle "Card" visive invece di una tabella
cols = st.columns(2)
for idx, row in df_pillars.iterrows():
    # Logica semaforo
    trend = row['Trend Lungo']
    score = row['Forza (-10/+10)']
    
    status = "NEUTRO"
    color = "gray"
    action = "Mantieni posizione"
    
    if trend == "RIALSISTA" and score > 0:
        status = "ACCUMULARE"
        color = "green"
        action = "Il trend è forte. Puoi aumentare l'esposizione o entrare sui ritracciamenti."
    elif trend == "RIBASSISTA":
        status = "DIFENSIVO / RIDURRE"
        color = "red"
        action = "Il trend è rotto. Non comprare, valuta di ridurre l'esposizione o attendere."
    
    with cols[idx % 2]:
        with st.container(border=True):
            st.subheader(f"{row['Nome Asset']}")
            st.metric("Forza Attuale", f"{score}/10", row['Perf. 1 Mese'])
            st.markdown(f"**Stato:** :{color}[{status}]")
            st.caption(action)
