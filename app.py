import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.set_page_config(page_title="Gold Carry Pro (NSE)", page_icon="🪙", layout="wide")

# --- 1. THE NSE-SPECIFIC MAPPING ---
# These are mapped to pull from the NSE feed for better liquidity discovery
MC_MAP = {
    "SGBJUN31I": "SGB54", "SGBJUN27": "SGB15", "SGBMAY26": "SGB10", 
    "SGBSEP31II": "SGB55", "SGBFEB32IV": "SGB58", "SGBDEC26": "SGBDE7654",
    "SGBJAN27": "SGBJA8308", "SGBNOV26": "SGBNO6355", "SGBJUL27": "SGB12",
    "SGBMAR28X": "SGB20", "SGBMAY28": "SGB25", "SGBOCT27": "SGB19",
    "SGBFEB27": "SGBFE8766", "SGBAPR28I": "SGB24", "SGBAUG27": "SGB13"
}

@st.cache_data(ttl=600)
def get_gold_spot():
    try:
        # Global Gold + USDINR = True Indian Spot
        gold = yf.Ticker("GC=F").fast_info['last_price']
        usdinr = yf.Ticker("INR=X").fast_info['last_price']
        return (gold / 31.1035) * usdinr
    except:
        return 0.0

@st.cache_data(ttl=600)
def get_mc_nse_offer(nse_symbol):
    mc_code = MC_MAP.get(nse_symbol)
    if not mc_code:
        return 0.0
    
    # Strictly hitting the NSE Pricefeed for better discovery
    url = f"https://priceapi.moneycontrol.com/pricefeed/nse/equitycash/{mc_code}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        
        # OPrice = Best Offer (Ask), pricecurrent = LTP
        offer = float(data['data'].get('OPrice', 0.0))
        ltp = float(data['data'].get('pricecurrent', 0.0))
        
        # Return Best Offer if available, else LTP
        return offer if offer > 0 else ltp
    except:
        return 0.0

live_spot = get_gold_spot()

# --- 2. SIDEBAR ---
st.sidebar.header("⚙️ NSE Portfolio Settings")
my_sgb_qty = st.sidebar.number_input("SGB Units", value=0, step=8)
my_sgb_cost = st.sidebar.number_input("SGB Cost (per gram)", value=0.0, format="%.2f")
my_mcx_lots = st.sidebar.number_input("Guinea Lots", value=0, step=1)
my_guinea_sell_lot = st.sidebar.number_input("Short Entry (per lot)", value=0.0, format="%.2f")

st.sidebar.divider()
st.sidebar.header("📈 Live MCX Price")
live_guinea_lot_ltp = st.sidebar.number_input("Live Guinea LTP", value=0.0, format="%.2f")

# API Logic
api_sgb_price = get_mc_nse_offer("SGBJUN31I")
manual_sgb_price = st.sidebar.number_input("Manual SGB Override", value=0.0, format="%.2f")
live_sgb_price = manual_sgb_price if manual_sgb_price > 0 else api_sgb_price

# --- 3. MAIN DASHBOARD ---
st.title("🪙 Gold Guinea Carry Tracker")
st.caption(f"Last updated: {pd.Timestamp.now().strftime('%H:%M:%S')} (NSE Data)")

if my_sgb_qty > 0 and my_mcx_lots > 0 and live_sgb_price > 0 and live_guinea_lot_ltp > 0:
    sgb_pnl = (live_sgb_price - my_sgb_cost) * my_sgb_qty
    mcx_pnl = (my_guinea_sell_lot - live_guinea_lot_ltp) * my_mcx_lots
    total_net = sgb_pnl + mcx_pnl

    c1, c2, c3 = st.columns(3)
    c1.metric("SGB P&L", f"₹{sgb_pnl:,.2f}", f"NSE: ₹{live_sgb_price:,.2f}")
    c2.metric("MCX P&L", f"₹{mcx_pnl:,.2f}", f"Lot: ₹{live_guinea_lot_ltp:,.2f}", delta_color="inverse")
    c3.metric("NET PROFIT", f"₹{total_net:,.2f}", "Total Spread")
else:
    st.info("👈 Enter trade details in the sidebar. Data refreshes every 10 mins.")

st.divider()

# --- 4. SCANNER (NSE) ---
st.subheader("🔍 NSE SGB Discount Scanner")
watch_list = ["SGBJUN31I", "SGBJUN27", "SGBMAY26", "SGBSEP31II"]
results = []

if live_spot > 0:
    st.write(f"*Calculated against Live Gold Spot: **₹{live_spot:,.2f} / gram***")
    for sgb in watch_list:
        price = get_mc_nse_offer(sgb)
        if price > 0:
            disc = ((live_spot - price) / live_spot) * 100
            results.append({
                "Series": sgb, 
                "NSE Offer Rate": f"₹{price:,.2f}", 
                "True Discount": f"{disc:.2f}%"
            })

    if results:
        st.table(pd.DataFrame(results))
    else:
        st.warning("⚠️ NSE API returned no data. Markets might be volatile.")
else:
    st.error("⚠️ Failed to fetch Global Spot Gold.")
