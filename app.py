import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.set_page_config(page_title="Gold Carry Pro", page_icon="🪙", layout="wide")

# --- 1. MAPPING & SETTINGS ---
SGB_MAP = {
    "SGBJUN31I": "SGB54", "SGBJUN27": "SGB15", "SGBMAY26": "SGB10", 
    "SGBSEP31II": "SGB55", "SGBFEB32IV": "SGB58", "SGBDEC26": "SGBDE7654"
}

# --- 2. DATA ENGINES (10-Min Pulse) ---
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
    url = "https://priceapi.moneycontrol.com/pricefeed/mcx/futures/MGG01" 
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5).json()
        price = float(res['data'].get('buyprice', 0.0))
        if price == 0: 
            price = float(res['data'].get('pricecurrent', 0.0))
        return price
    except: return 0.0

# Pre-fetch Data
live_spot = get_gold_spot()
auto_guinea = get_mc_guinea_price()
auto_sgb = get_mc_sgb_price("SGBJUN31I")

# --- 3. SIDEBAR ---
st.sidebar.header("⚙️ Portfolio Settings")
my_sgb_qty = st.sidebar.number_input("SGB Units", value=24)
my_sgb_cost = st.sidebar.number_input("SGB Cost Avg", value=15906.67)
my_mcx_lots = st.sidebar.number_input("Guinea Lots Short", value=3)
my_guinea_entry = st.sidebar.number_input("Short Entry (Per Lot)", value=131600.0)

st.sidebar.divider()
st.sidebar.header("🔄 Manual Overrides")
manual_sgb = st.sidebar.number_input("SGB Override Price", value=0.0)
manual_mcx = st.sidebar.number_input("MCX Override Price", value=0.0)

final_sgb = manual_sgb if manual_sgb > 0 else auto_sgb
final_mcx = manual_mcx if manual_mcx > 0 else auto_guinea

# --- 4. MAIN DASHBOARD ---
st.title("🪙 Gold Guinea Carry Tracker")
st.caption(f"Sync: {pd.Timestamp.now().strftime('%H:%M:%S')} (10-Min Cache)")

if final_sgb > 0 and final_mcx > 0:
    sgb_pnl = (final_sgb - my_sgb_cost) * my_sgb_qty
    mcx_pnl = (my_guinea_entry - final_mcx) * my_mcx_lots
    net_pnl = sgb_pnl + mcx_pnl

    c1, c2, c3 = st.columns(3)
    c1.metric("SGB P&L", f"₹{sgb_pnl:,.0f}", f"NSE: ₹{final_sgb:,.0f}")
    c2.metric("MCX P&L", f"₹{mcx_pnl:,.0f}", f"Lot: ₹{final_mcx:,.0f}", delta_color="inverse")
    c3.metric("NET PROFIT", f"₹{net_pnl:,.0f}", "Live Combined Spread")
else:
    st.warning("⚠️ Fetching live prices... use sidebar if market is closed.")

st.divider()

# --- 5. THE SWAP SCANNER ---
st.subheader("🔍 SGB Swap & Discount Scanner")
watch_list = ["SGBJUN31I", "SGBJUN27", "SGBMAY26", "SGBSEP31II"]
results = []

if live_spot > 0:
    st.write(f"Global Spot: **₹{live_spot:,.2f}**")
    for sgb in watch_list:
        price = get_mc_sgb_price(sgb)
        if price > 0:
            disc = ((live_spot - price) / live_spot) * 100
            
            # THE SWAP MATH:
            # (Current SGB Price - Target SGB Price) * Your Qty
            # This is the cash you "unlock" by switching.
            swap_profit = (final_sgb - price) * my_qty_target if 'my_qty_target' in locals() else (final_sgb - price) * my_sgb_qty
            
            results.append({
                "Series": sgb, 
                "Price": f"₹{price:,.0f}", 
                "Discount": f"{disc:.2f}%",
                "Swap Profit": f"₹{swap_profit:,.0f}" if sgb != "SGBJUN31I" else "Current"
            })
    
    if results:
        # Style the table to highlight profits
        df = pd.DataFrame(results)
        st.table(df)
        st.info("💡 **Tip:** 'Swap Profit' is the extra cash you get by selling your current SGB and buying the target series.")
else:
    st.info("Fetching market data...")
