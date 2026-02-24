import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.set_page_config(page_title="Gold Carry Pro (All-Auto)", page_icon="🪙", layout="wide")

# --- 1. MAPPING CODES ---
SGB_MAP = {
    "SGBJUN31I": "SGB54", "SGBJUN27": "SGB15", "SGBMAY26": "SGB10", 
    "SGBSEP31II": "SGB55", "SGBFEB32IV": "SGB58", "SGBDEC26": "SGBDE7654"
    # (Other SGBs from your previous list can be added here)
}

# MCX Gold Guinea Code (Moneycontrol uses 'MGG01' or similar for the near-month)
MCX_GUINEA_CODE = "MGG01" 

# --- 2. DATA ENGINES (10-Min Cache) ---
@st.cache_data(ttl=600)
def get_gold_spot():
    try:
        gold = yf.Ticker("GC=F").fast_info['last_price']
        usdinr = yf.Ticker("INR=X").fast_info['last_price']
        return (gold / 31.1035) * usdinr
    except: return 0.0

@st.cache_data(ttl=600)
def get_mc_sgb_price(nse_symbol):
    mc_code = SGB_MAP.get(nse_symbol)
    if not mc_code: return 0.0
    url = f"https://priceapi.moneycontrol.com/pricefeed/nse/equitycash/{mc_code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5).json()
        offer = float(res['data'].get('OPrice', 0.0))
        ltp = float(res['data'].get('pricecurrent', 0.0))
        return offer if offer > 0 else ltp
    except: return 0.0

@st.cache_data(ttl=600)
def get_mc_guinea_price():
    # Dedicated Commodity Feed for MCX
    url = f"https://priceapi.moneycontrol.com/pricefeed/mcx/futures/{MCX_GUINEA_CODE}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5).json()
        # For a short position, we care about the 'Buy Price' (what we pay to exit)
        buy_back_price = float(res['data'].get('buyprice', 0.0))
        ltp = float(res['data'].get('pricecurrent', 0.0))
        return buy_back_price if buy_back_price > 0 else ltp
    except: return 0.0

# Pre-fetch Live Data
live_spot = get_gold_spot()
auto_guinea_ltp = get_mc_guinea_price()
auto_sgb_ltp = get_mc_sgb_price("SGBJUN31I")

# --- 3. SIDEBAR ---
st.sidebar.header("⚙️ Portfolio Settings")
my_sgb_qty = st.sidebar.number_input("SGB Units", value=24)
my_sgb_cost = st.sidebar.number_input("SGB Cost Avg", value=15906.67)

my_mcx_lots = st.sidebar.number_input("Guinea Lots Short", value=3)
my_guinea_short_entry = st.sidebar.number_input("Short Entry (per lot)", value=131600.0)

st.sidebar.divider()
st.sidebar.header("🔄 Live Overrides")
# If the API fails, you can still type it in manually
manual_sgb = st.sidebar.number_input("Manual SGB Price", value=0.0)
manual_mcx = st.sidebar.number_input("Manual MCX Price", value=0.0)

live_sgb = manual_sgb if manual_sgb > 0 else auto_sgb_ltp
live_mcx = manual_mcx if manual_mcx > 0 else auto_guinea_ltp

# --- 4. MAIN DASHBOARD ---
st.title("🪙 Gold Guinea Carry Tracker")
st.caption(f"Last Sync: {pd.Timestamp.now().strftime('%H:%M')} (10-Min Cache)")

if live_sgb > 0 and live_mcx > 0:
    # THE MATH
    sgb_pnl = (live_sgb - my_sgb_cost) * my_sgb_qty
    mcx_pnl = (my_guinea_short_entry - live_mcx) * my_mcx_lots
    total_net = sgb_pnl + mcx_pnl

    c1, c2, c3 = st.columns(3)
    c1.metric("SGB P&L", f"₹{sgb_pnl:,.0f}", f"Offer: ₹{live_sgb:,.0f}")
    c2.metric("MCX P&L", f"₹{mcx_pnl:,.0f}", f"Lot: ₹{live_mcx:,.0f}", delta_color="inverse")
    c3.metric("NET PROFIT", f"₹{total_net:,.0f}", "Total Locked Carry")
else:
    st.error("⚠️ Failed to fetch live prices. Please check internet or use Manual Overrides.")

st.divider()

# --- 5. SCANNER ---
st.subheader("🔍 SGB Market Scanner")
watch_list = ["SGBJUN31I", "SGBJUN27", "SGBMAY26"]
results = []
for sgb in watch_list:
    price = get_mc_sgb_price(sgb)
    if price > 0 and live_spot > 0:
        disc = ((live_spot - price) / live_spot) * 100
        results.append({"Series": sgb, "NSE Offer": f"₹{price:,.0f}", "Discount": f"{disc:.2f}%"})

if results:
    st.table(pd.DataFrame(results))
