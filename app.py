import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Strategic Terminal v16.0", layout="wide")
st.markdown("""
<style>
    .stButton>button { width: 100%; padding: 0px; height: 1.8em; font-size: 0.8rem; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.2rem; }
    .sub-row { background-color: #f9f9f9; padding: 5px; border-radius: 5px; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# --- STATO NAVIGAZIONE ---
if 'expanded_id' not in st.session_state: st.session_state.expanded_id = None

# --- DATABASE COMPLETO (15+ GEO, 15+ SETTORI) ---
db = {
    "GEO": {
        "USA (S&P 500)": {
            "p": "SPY",
            "etfs": [
                {"n": "Vanguard S&P 500", "t": "VOO", "isin": "US9229083632"},
                {"n": "Invesco S&P 500 Equal W.", "t": "RSP", "isin": "US46137V3574"},
                {"n": "iShares Core S&P 500", "t": "IVV", "isin": "US4642872000"}
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
        "Europa (Aggregato)": {
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
        "Germania": {
            "p": "EWG",
            "etfs": [
                {"n": "iShares MSCI Germany", "t": "EWG", "isin": "US4642868065"},
                {"n": "Global X DAX Germany", "t": "DAX", "isin": "US37954Y6656"},
                {"n": "Franklin FTSE Germany", "t": "FLGR", "isin": "US3535163070"}
            ],
            "stocks": [
                {"n": "SAP SE (ADR)", "t": "SAP", "isin": "US8030542042"},
                {"n": "Siemens AG (ADR)", "t": "SIEGY", "isin": "US8261975010"},
                {"n": "Deutsche Telekom", "t": "DTEGY", "isin": "US2515661054"}
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
        "Regno Unito": {
            "p": "EWU",
            "etfs": [
                {"n": "iShares MSCI UK", "t": "EWU", "isin": "US4642867075"},
                {"n": "Franklin FTSE UK", "t": "FLGB", "isin": "US3535164060"},
                {"n": "First Trust UK Alpha", "t": "FKU", "isin": "US33733E3014"}
            ],
            "stocks": [
                {"n": "AstraZeneca", "t": "AZN", "isin": "US0463531089"},
                {"n": "Shell PLC", "t": "SHEL", "isin": "US7802593050"},
                {"n": "HSBC Holdings", "t": "HSBC", "isin": "US4042804066"}
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
        "Svizzera": {
            "p": "EWL",
            "etfs": [
                {"n": "iShares MSCI Switzerland", "t": "EWL", "isin": "US4642867497"},
                {"n": "Franklin FTSE Switzerland", "t": "FLSW", "isin": "US3535165059"},
                {"n": "First Trust Switzerland", "t": "FSZ", "isin": "US3373673026"}
            ],
            "stocks": [
                {"n": "Nestle (OTC)", "t": "NSRGY", "isin": "US6410694060"},
                {"n": "Novartis", "t": "NVS", "isin": "US66987V1098"},
                {"n": "UBS Group", "t": "UBS", "isin": "CH0244767585"}
            ]
        },
        "Brasile": {
            "p": "EWZ",
            "etfs": [
                {"n": "iShares MSCI Brazil", "t": "EWZ", "isin": "US4642864007"},
                {"n": "Franklin FTSE Brazil", "t": "FLBR", "isin": "US3535166040"},
                {"n": "VanEck Brazil Small-Cap", "t": "BRF", "isin": "US92189F8251"}
            ],
            "stocks": [
                {"n": "Petrobras", "t": "PBR", "isin": "US71654V4086"},
                {"n": "Vale SA", "t": "VALE", "isin": "US91912E1055"},
                {"n": "Nu Holdings", "t": "NU", "isin": "KYG6683N1034"}
            ]
        },
        "Taiwan": {
            "p": "EWT",
            "etfs": [
                {"n": "iShares MSCI Taiwan", "t": "EWT", "isin": "US46434G7723"},
                {"n": "Franklin FTSE Taiwan", "t": "FLTW", "isin": "US3535167030"},
                {"n": "First Trust Taiwan", "t": "FTW", "isin": "US33734X1928"}
            ],
            "stocks": [
                {"n": "TSMC", "t": "TSM", "isin": "US8740391003"},
                {"n": "United Microelectronics", "t": "UMC", "isin": "US9108734057"},
                {"n": "ASE Technology", "t": "ASX", "isin": "US00215W1009"}
            ]
        },
        "Corea del Sud": {
            "p": "EWY",
            "etfs": [
                {"n": "iShares MSCI South Korea", "t": "EWY", "isin": "US4642867729"},
                {"n": "Franklin FTSE South Korea", "t": "FLKR", "isin": "US3535168020"},
                {"n": "First Trust South Korea", "t": "FKO", "isin": "US33734X1019"}
            ],
            "stocks": [
                {"n": "POSCO Holdings", "t": "PKX", "isin": "US6934831099"},
                {"n": "KB Financial", "t": "KB", "isin": "US4824151042"},
                {"n": "SK Telecom", "t": "SKM", "isin": "US78440P1084"}
            ]
        },
        "Canada": {
            "p": "EWC",
            "etfs": [
                {"n": "iShares MSCI Canada", "t": "EWC", "isin": "US4642865095"},
                {"n": "Franklin FTSE Canada", "t": "FLCA", "isin": "US3535161090"},
                {"n": "JPMorgan BetaBuilders CA", "t": "BBCA", "isin": "US46641Q4073"}
            ],
            "stocks": [
                {"n": "Royal Bank of Canada", "t": "RY", "isin": "CA7800871021"},
                {"n": "Toronto-Dominion Bank", "t": "TD", "isin": "CA8911605092"},
                {"n": "Shopify", "t": "SHOP", "isin": "CA82509L1076"}
            ]
        },
        "Australia": {
            "p": "EWA",
            "etfs": [
                {"n": "iShares MSCI Australia", "t": "EWA", "isin": "US4642861037"},
                {"n": "Franklin FTSE Australia", "t": "FLAU", "isin": "US3535165059"},
                {"n": "WisdomTree Australia Div", "t": "AUSE", "isin": "US97717X7272"}
            ],
            "stocks": [
                {"n": "BHP Group", "t": "BHP", "isin": "US0886061086"},
                {"n": "Rio Tinto", "t": "RIO", "isin": "US7672041008"},
                {"n": "Westpac Banking", "t": "WBK", "isin": "US9612143018"}
            ]
        },
        "Messico": {
            "p": "EWW",
            "etfs": [
                {"n": "iShares MSCI Mexico", "t": "EWW", "isin": "US4642868222"},
                {"n": "Franklin FTSE Mexico", "t": "FLMX", "isin": "US3535166040"},
                {"n": "Direxion Daily Mexico", "t": "MEXX", "isin": "US25460E5399"}
            ],
            "stocks": [
                {"n": "America Movil", "t": "AMX", "isin": "US02364W1053"},
                {"n": "Fomento Economico", "t": "FMX", "isin": "US3444191064"},
                {"n": "Cemex", "t": "CX", "isin": "US1512908898"}
            ]
        }
    },
    "SECTOR": {
        "Technology": {
            "p": "XLK",
            "etfs": [{"n": "Tech Select Sector", "t": "XLK", "isin": "US81369Y8030"}, {"n": "Vanguard Info Tech", "t": "VGT", "isin": "US92204A7028"}, {"n": "Fidelity MSCI Tech", "t": "FTEC", "isin": "US3160922934"}],
            "stocks": [{"n": "Microsoft", "t": "MSFT", "isin": "US5949181045"}, {"n": "Apple", "t": "AAPL", "isin": "US0378331005"}, {"n": "NVIDIA", "t": "NVDA", "isin": "US67066G1040"}]
        },
        "Semiconductors": {
            "p": "SMH",
            "etfs": [{"n": "VanEck Semiconductor", "t": "SMH", "isin": "US92189F6768"}, {"n": "iShares Semiconductor", "t": "SOXX", "isin": "US4642875235"}, {"n": "SPDR S&P Semiconductor", "t": "XSD", "isin": "US78464A8624"}],
            "stocks": [{"n": "NVIDIA", "t": "NVDA", "isin": "US67066G1040"}, {"n": "Broadcom", "t": "AVGO", "isin": "US11135F1012"}, {"n": "AMD", "t": "AMD", "isin": "US0079031078"}]
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
        "Financials": {
            "p": "XLF",
            "etfs": [{"n": "Financial Select", "t": "XLF", "isin": "US81369Y6059"}, {"n": "Vanguard Financials", "t": "VFH", "isin": "US92204A4058"}, {"n": "SPDR S&P Bank", "t": "KBE", "isin": "US78464A7972"}],
            "stocks": [{"n": "JPMorgan Chase", "t": "JPM", "isin": "US46625H1005"}, {"n": "Berkshire Hathaway", "t": "BRK-B", "isin": "US0846707026"}, {"n": "Visa", "t": "V", "isin": "US92826C8394"}]
        },
        "Defense & Aerospace": {
            "p": "ITA",
            "etfs": [{"n": "iShares US Aerospace", "t": "ITA", "isin": "US4642887602"}, {"n": "Invesco Aerospace", "t": "PPA", "isin": "US46137V1008"}, {"n": "SPDR Aerospace & Def", "t": "XAR", "isin": "US78464A6644"}],
            "stocks": [{"n": "RTX Corp", "t": "RTX", "isin": "US75513E1010"}, {"n": "Lockheed Martin", "t": "LMT", "isin": "US5398301094"}, {"n": "General Dynamics", "t": "GD", "isin": "US3695501086"}]
        },
        "Gold Miners": {
            "p": "GDX",
            "etfs": [{"n": "VanEck Gold Miners", "t": "GDX", "isin": "US92189F1066"}, {"n": "VanEck Junior Miners", "t": "GDXJ", "isin": "US92189F7915"}, {"n": "iShares MSCI Global Gold", "t": "RING", "isin": "US46434V6130"}],
            "stocks": [{"n": "Newmont", "t": "NEM", "isin": "US6516391066"}, {"n": "Barrick Gold", "t": "GOLD", "isin": "CA0679011084"}, {"n": "Agnico Eagle", "t": "AEM", "isin": "CA0084741085"}]
        },
        "Uranium & Nuclear": {
            "p": "URA",
            "etfs": [{"n": "Global X Uranium", "t": "URA", "isin": "US37954Y8710"}, {"n": "Sprott Uranium Miners", "t": "URNM", "isin": "US85208P3038"}, {"n": "VanEck Uranium", "t": "NLR", "isin": "US92189F6016"}],
            "stocks": [{"n": "Cameco", "t": "CCJ", "isin": "CA13321L1085"}, {"n": "NexGen Energy", "t": "NXE", "isin": "CA65340P1062"}, {"n": "Uranium Energy", "t": "UEC", "isin": "US9168961038"}]
        },
        "Cybersecurity": {
            "p": "CIBR",
            "etfs": [{"n": "First Trust Cyber", "t": "CIBR", "isin": "US33734X8469"}, {"n": "ETFMG Prime Cyber", "t": "HACK", "isin": "US26923J5099"}, {"n": "Global X Cyber", "t": "BUG", "isin": "US37954Y6409"}],
            "stocks": [{"n": "Palo Alto Networks", "t": "PANW", "isin": "US6974351057"}, {"n": "CrowdStrike", "t": "CRWD", "isin": "US22788C1053"}, {"n": "Fortinet", "t": "FTNT", "isin": "US34959E1091"}]
        },
        "Robotics & AI": {
            "p": "BOTZ",
            "etfs": [{"n": "Global X Robotics & AI", "t": "BOTZ", "isin": "US37954Y7159"}, {"n": "ROBO Global Robotics", "t": "ROBO", "isin": "US3015057074"}, {"n": "iShares Robotics", "t": "IRBO", "isin": "US46435U1369"}],
            "stocks": [{"n": "UiPath", "t": "PATH", "isin": "US90364P1057"}, {"n": "Intuitive Surgical", "t": "ISRG", "isin": "US4612021034"}, {"n": "Teradyne", "t": "TER", "isin": "US8807701029"}]
        },
        "Biotech": {
            "p": "IBB",
            "etfs": [{"n": "iShares Biotechnology", "t": "IBB", "isin": "US4642875565"}, {"n": "SPDR S&P Biotech", "t": "XBI", "isin": "US78464A8707"}, {"n": "Ark Genomic", "t": "ARKG", "isin": "US00214Q3020"}],
            "stocks": [{"n": "Vertex Pharm.", "t": "VRTX", "isin": "US92532F1003"}, {"n": "Regeneron", "t": "REGN", "isin": "US75886F1075"}, {"n": "Amgen", "t": "AMGN", "isin": "US0311621009"}]
        },
        "Consumer Staples": {
            "p": "XLP",
            "etfs": [{"n": "Staples Select Sector", "t": "XLP", "isin": "US81369Y3080"}, {"n": "Vanguard Staples", "t": "VDC", "isin": "US92204A2078"}, {"n": "iShares Global Staples", "t": "KXI", "isin": "US4642873172"}],
            "stocks": [{"n": "Procter & Gamble", "t": "PG", "isin": "US7427181091"}, {"n": "Costco", "t": "COST", "isin": "US22160K1051"}, {"n": "Coca-Cola", "t": "KO", "isin": "US1912161007"}]
        },
        "Real Estate": {
            "p": "XLRE",
            "etfs": [{"n": "Real Estate Select", "t": "XLRE", "isin": "US81369Y8600"}, {"n": "Vanguard Real Estate", "t": "VNQ", "isin": "US9229085538"}, {"n": "Schwab US REIT", "t": "SCHH", "isin": "US8085248472"}],
            "stocks": [{"n": "Prologis", "t": "PLD", "isin": "US74340W1036"}, {"n": "American Tower", "t": "AMT", "isin": "US03027X1000"}, {"n": "Equinix", "t": "EQIX", "isin": "US29444U7000"}
            ]
        },
        "Utilities": {
            "p": "XLU",
            "etfs": [{"n": "Utilities Select", "t": "XLU", "isin": "US81369Y8865"}, {"n": "Vanguard Utilities", "t": "VPU", "isin": "US92204A6038"}, {"n": "Fidelity Utilities", "t": "FUTY", "isin": "US3160925093"}],
            "stocks": [{"n": "NextEra Energy", "t": "NEE", "isin": "US65339F1012"}, {"n": "Southern Co", "t": "SO", "isin": "US8425871071"}, {"n": "Duke Energy", "t": "DUK", "isin": "US26441C2044"}]
        },
        "Materials": {
            "p": "XLB",
            "etfs": [{"n": "Materials Select", "t": "XLB", "isin": "US81369Y1001"}, {"n": "Vanguard Materials", "t": "VAW", "isin": "US92204A8018"}, {"n": "iShares Global Mat.", "t": "MXI", "isin": "US4642872919"}],
            "stocks": [{"n": "Linde", "t": "LIN", "isin": "IE00BZ12WP82"}, {"n": "Freeport-McMoRan", "t": "FCX", "isin": "US35671D8570"}, {"n": "Sherwin-Williams", "t": "SHW", "isin": "US8243481061"}]
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
    """Scarica dati. Se fallisce, RITORNA DEFAULT (N/A) invece di None."""
    try:
        # Time.sleep per rate limit
        time.sleep(0.05)
        df = yf.download(ticker, period="2y", progress=False)
        
        if df.empty or len(df) < 50:
            raise Exception("No Data")
        
        # Gestione dataframe
        try: closes = df['Close'].iloc[:, 0]
        except: closes = df['Close']
            
        curr = float(closes.iloc[-1])
        
        def get_px(d):
            idx = -d if len(closes) > d else 0
            return float(closes.iloc[idx])
            
        p1m, p3m, p6m, p1y = get_px(22), get_px(65), get_px(130), get_px(252)
        
        perf_1m = ((curr - p1m)/p1m)*100
        perf_3m = ((curr - p3m)/p3m)*100
        perf_6m = ((curr - p6m)/p6m)*100
        perf_1y = ((curr - p1y)/p1y)*100
        
        # Score
        w_perf = (perf_3m*0.4) + (perf_1m*0.3) + (perf_6m*0.2) + (perf_1y*0.1)
        score = max(min(w_perf / 3.0, 10), -10)
        
        return {
            "score": score,
            "p1m": perf_1m, "p3m": perf_3m, "p6m": perf_6m, "p1y": perf_1y,
            "price": curr, "valid": True
        }
    except:
        # FAIL-SAFE: Ritorna dati vuoti ma "validi" per la visualizzazione
        return {
            "score": 0, "p1m": 0, "p3m": 0, "p6m": 0, "p1y": 0, "price": 0,
            "valid": False # Flag per indicare che il dato è finto
        }

# --- UI COMPONENTS ---
def color_val(val, is_valid):
    if not is_valid: return "N/A"
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
    
    items = list(db[section_key].items())
    
    # Progress Bar per caricamento iniziale
    prog = st.progress(0)
    for i, (name, data) in enumerate(items):
        # Analisi del Proxy (Capogruppo)
        stats = analyze_ticker(data['p'])
        
        # Visualizzazione Riga
        c1, c2, c3, c4, c5, c6, c7 = st.columns([3, 1, 1, 1, 1, 1, 1])
        
        # Icona Score
        score = stats['score']
        valid = stats['valid']
        
        if valid:
            icon = "🔥" if score > 7 else ("❄️" if score < -7 else "➖")
            sc_col = "green" if score > 0 else "red"
            score_txt = f":{sc_col}[**{score:.1f}**]"
        else:
            icon = "⚠️"
            score_txt = "N/A"

        c1.markdown(f"**{icon} {name}**")
        c2.markdown(score_txt)
        c3.markdown(color_val(stats['p1m'], valid))
        c4.markdown(color_val(stats['p3m'], valid))
        c5.markdown(color_val(stats['p6m'], valid))
        c6.markdown(color_val(stats['p1y'], valid))
        
        # Bottone Espansione
        is_expanded = (st.session_state.expanded_id == name)
        label = "⬇️ Dettagli" if not is_expanded else "❌ Chiudi"
        
        if c7.button(label, key=f"btn_{name}"):
            st.session_state.expanded_id = name if not is_expanded else None
            st.rerun()
            
        # SPACCATO (Caricato SOLO se espanso)
        if is_expanded:
            with st.container(border=True):
                st.markdown(f"#### 🔎 Analisi Approfondita: {name}")
                
                # Combiniamo ETF e Stocks
                sub_assets = []
                if 'etfs' in data: sub_assets += data['etfs']
                if 'stocks' in data: sub_assets += data['stocks']
                if 'alts' in data: sub_assets += data['alts']
                
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
                
                # Loop sui 6 asset
                for asset in sub_assets:
                    # Scarichiamo dati (o N/A se fallisce)
                    s_stats = analyze_ticker(asset['t'])
                    
                    sc1, sc2, sc3, sc4, sc5, sc6, sc7, sc8 = st.columns([2, 1, 2, 1, 1, 1, 1, 1])
                    sc1.write(f"**{asset['n']}**")
                    sc2.write(f"`{asset['t']}`")
                    sc3.write(f"{asset['isin']}")
                    
                    if s_stats['valid']:
                        sc4.write(f"${s_stats['price']:.2f}")
                        sc5.markdown(color_val(s_stats['p1m'], True))
                        sc6.markdown(color_val(s_stats['p6m'], True))
                        sc7.markdown(color_val(s_stats['p1y'], True))
                    else:
                        sc4.write("N/A")
                        sc5.write("-")
                        sc6.write("-")
                        sc7.write("-")
                        
                    sc8.link_button("🌐", f"https://finance.yahoo.com/quote/{asset['t']}")
                    
        prog.progress((i+1)/len(items))
    prog.empty()

# --- MAIN ---
st.title("🌍 Strategic Terminal v16.0")
st.caption("Database Completo (15+ Nazioni) • Fail-Safe Attivo • ISIN Inclusi")

if st.button("🔄 AGGIORNA DATI"):
    st.cache_data.clear()
    st.rerun()

render_section("GEO", "1. 🗺️ CLASSIFICA NAZIONI")
st.markdown("---")
render_section("SECTOR", "2. 🏭 CLASSIFICA SETTORI")
st.markdown("---")
render_section("PILLARS", "3. 🏛️ I 4 PILASTRI STRATEGICI")
