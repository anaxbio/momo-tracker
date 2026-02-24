import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.set_page_config(page_title="Gold Carry Pro", page_icon="🪙", layout="wide")

# --- 1. MAPPING & SETTINGS ---
# Using the full list provided earlier
MC_MAP = {
    "SGBNOV25VI": "SGBNO398", "SGBDEC2512": "SGBDE795", "SGBDEC25XI": "SGBDE729", 
    "SGBDEC2513": "SGBDE862", "SGBJUN27": "SGB15", "SGBOCT25V": "SGBOC355", 
    "SGBDEC25": "SGBDE623", "SGBDE30III": "SGB52", "SGBDEC26": "SGBDE7654", 
    "SGBFEB29XI": "SGB35", "SGBMAR31IV": "SGB53", "SGBMAR30X": "SGB49", 
    "SGBJUN30": "SGB50", "SGBFEB32IV": "SGB58", "SGBAUG30": "SGB51", 
    "SGBJAN30IX": "SGB48", "SGBJUN29I": "GB202", "SGBOCT27VI": "SGB16", 
    "SGBDE31III": "SGB57", "SGBSEP31II": "SGB55", "SGBDC27VII": "SGB17", 
    "SGBSEP28VI": "SGB29", "SGBJAN26": "SGBJA945", "SGBJ28VIII": "SGB18", 
    "SGBNOV25": "SGBNO458", "SGBJUL29IV": "SGB39", "SGBJAN29X": "SGB34", 
    "SGBNV29VII": "SGB44", "SGBD29VIII": "SGB46", "SGBMAY29I": "GB201", 
    "SGBMR29XII": "SGB36", "SGBJUL27": "SGB12", "SGBSEP29VI": "SGB42", 
    "SGBJAN29IX": "SGB33", "SGBJUN31I": "SGB54", "SGBFEB28IX": "SGB21", 
    "SGBOCT25IV": "SGB11", "SGBN28VIII": "SGB32", "SGBOCT25": "SGBOC250", 
    "SGBOC28VII": "SGB30", "SGBJUN28": "SGB26", "SGBJUL28IV": "SGB27", 
    "SGBAUG29V": "SGB40", "SGBOCT27": "SGB19", "SGBMAR28X": "SGB20", 
    "SGBMAY28": "SGB25", "SGBOCT26": "SGBOC5960", "SGBNOV258": "SGBNO497", 
    "SGBFEB27": "SGBFE8766", "SGBAPR28I": "SGB24", "SGBAUG27": "SGB13", 
    "SGBJU29III": "SGB37", "SGBAUG28V": "SGB28", "SGBSEP27": "SGB14", 
    "SGBJAN27": "SGBJA8308", "SGBNOV26": "SGBNO6355", "SGBMAY26": "SGB10", 
    "SGBNOV25IX": "SGBNO540"
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
def get_mc_sgb_offer(nse_symbol):
    mc_code = MC_MAP.get(nse_symbol)
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
    # YOUR SECRET API - Using the commodityfutures endpoint
    url = "https://priceapi.moneycontrol.com/pricefeed/mcx/commodityfutures/GOLDGUINEA?expiry=2026-03-31"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5).json()
        # For our short, we need the 'buyprice' (Offer) to see exit cost
        price = float(res['data'].get('buyprice', 0.0))
        if price == 0: 
            price = float(res['data'].get('pricecurrent', 0.0))
        return price
    except: return 0.0

# --- 3. SIDEBAR (Dynamic Settings) ---
st.sidebar.header("🎯 My Active Holding")
active_holding = st.sidebar.selectbox("Select Active SGB", options=list(MC_MAP.keys()), index=list(MC_MAP.keys()).index("SGBJUN31I"))

st.sidebar.divider()
st.sidebar.header("⚙️ Portfolio Settings")
my_sgb_qty = st.sidebar.number_input("SGB Units Held", value=24, step=8)
my_sgb_cost = st.sidebar.number_input("SGB Avg Cost", value=15906.67, format="%.2f")
my_mcx_lots = st.sidebar.number_input("Guinea Lots Short", value=3, step=1)
my_guinea_entry = st.sidebar.number_input("Short Entry (Lot)", value=131600.0, format="%.2f")

# Data Pulse
live_spot = get_gold_spot()
auto_guinea = get_mc_guinea_price()
auto_sgb = get_mc_sgb_offer(active_holding)

st.sidebar.divider()
st.sidebar.header("🔄 Manual Overrides")
manual_sgb = st.sidebar.number_input("Override SGB Price", value=0.0, format="%.2f")
manual_mcx = st.sidebar.number_input("Override MCX Price", value=0.0, format="%.2f")

final_sgb = manual_sgb if manual_sgb > 0 else auto_sgb
final_mcx = manual_mcx if manual_mcx > 0 else auto_guinea

# --- 4. MAIN DASHBOARD ---
st.title("🪙 Gold Guinea Carry Tracker")
st.caption(f"Sync: {pd.Timestamp.now().strftime('%H:%M:%S')} (NSE & MCX Live)")

if final_sgb > 0 and final_mcx > 0:
    sgb_pnl = (final_sgb - my_sgb_cost) * my_sgb_qty
    mcx_pnl = (my_guinea_entry - final_mcx) * my_mcx_lots
    net_pnl = sgb_pnl + mcx_pnl

    c1, c2, c3 = st.columns(3)
    c1.metric(f"SGB P&L ({active_holding})", f"₹{sgb_pnl:,.0f}", f"Rate: ₹{final_sgb:,.0f}")
    c2.metric("MCX P&L", f"₹{mcx_pnl:,.0f}", f"Lot: ₹{final_mcx:,.0f}", delta_color="inverse")
    c3.metric("NET PROFIT", f"₹{net_pnl:,.0f}", "Live Arbitrage")
else:
    st.warning("⚠️ Prices pending... Check sidebar.")

st.divider()

# --- 5. SWAP SCANNER (With NSE Logic) ---
st.subheader("🔍 Opportunity Scanner")
scan_list = ["SGBJUN31I", "SGBJUN27", "SGBMAY26", "SGBSEP31II"]
results = []

if live_spot > 0:
    st.write(f"Global Spot: **₹{live_spot:,.2f}**")
    for sgb in scan_list:
        # Check for individual scanner overrides to fix "Sense Check" errors
        with st.sidebar.expander(f"Sense Check: {sgb}"):
            s_override = st.number_input(f"Actual {sgb} Offer", value=0.0, key=f"s_{sgb}")
        
        price = s_override if s_override > 0 else get_mc_sgb_offer(sgb)
        
        if price > 0:
            disc = ((live_spot - price) / live_spot) * 100
            swap_benefit = (final_sgb - price) * my_sgb_qty
            results.append({
                "Series": sgb, 
                "Offer": f"₹{price:,.0f}", 
                "Discount": f"{disc:.2f}%",
                "Swap Profit": f"₹{swap_benefit:,.0f}" if sgb != active_holding else "★ ACTIVE"
            })
    
    st.table(pd.DataFrame(results))
