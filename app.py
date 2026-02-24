import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.set_page_config(page_title="Gold Carry Pro", page_icon="🪙", layout="wide")

# --- 1. THE "SECRET" MONEYCONTROL API ENGINE ---
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

@st.cache_data(ttl=3600)
def get_gold_spot():
    try:
        gold = yf.Ticker("GC=F").fast_info['last_price']
        usdinr = yf.Ticker("INR=X").fast_info['last_price']
        return (gold / 31.1035) * usdinr
    except:
        return 0.0

@st.cache_data(ttl=3600)
def get_mc_sgb_offer(nse_symbol):
    mc_code = MC_MAP.get(nse_symbol)
    if not mc_code:
        return 0.0
    url = f"https://priceapi.moneycontrol.com/pricefeed/nse/equitycash/{mc_code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        offer = float(data['data'].get('OPrice', 0.0))
        ltp = float(data['data'].get('pricecurrent', 0.0))
        return offer if offer > 0 else ltp
    except:
        return 0.0

live_spot = get_gold_spot()

# --- 2. SIDEBAR ---
st.sidebar.header("⚙️ Portfolio Settings")
my_sgb_qty = st.sidebar.number_input("SGB Units Bought", value=0, step=8)
my_sgb_cost = st.sidebar.number_input("SGB Avg Buy Price", value=0.0, format="%.2f")
my_mcx_lots = st.sidebar.number_input("Guinea Lots Sold", value=0, step=1)
my_guinea_sell_lot = st.sidebar.number_input("Guinea Short Avg (Entry)", value=0.0, format="%.2f")

st.sidebar.divider()
st.sidebar.header("📈 Live MCX Price")
live_guinea_lot_ltp = st.sidebar.number_input("Live Guinea Lot LTP", value=0.0, format="%.2f")

# Fetch API Price
api_sgb_price = get_mc_sgb_offer("SGBJUN31I")

st.sidebar.header("🔄 Manual SGB Override")
manual_sgb_price = st.sidebar.number_input("Override SGB Price", value=0.0, format="%.2f")
live_sgb_price = manual_sgb_price if manual_sgb_price > 0 else api_sgb_price

# --- 3. MAIN DASHBOARD ---
st.title("🪙 Gold Guinea Carry Tracker")

if my_sgb_qty > 0 and my_mcx_lots > 0 and live_sgb_price > 0 and live_guinea_lot_ltp > 0:
    sgb_pnl = (live_sgb_price - my_sgb_cost) * my_sgb_qty
    mcx_pnl = (my_guinea_sell_lot - live_guinea_lot_ltp) * my_mcx_lots
    total_net = sgb_pnl + mcx_pnl

    c1, c2, c3 = st.columns(3)
    c1.metric("SGB P&L", f"₹{sgb_pnl:,.2f}", delta=f"LTP: ₹{live_sgb_price:,.2f}")
    c2.metric("MCX P&L", f"₹{mcx_pnl:,.2f}", delta=f"Lot: ₹{live_guinea_lot_ltp:,.2f}", delta_color="inverse")
    c3.metric("NET PROFIT", f"₹{total_net:,.2f}", "Locked Carry")
else:
    st.info("👈 Please enter your details in the sidebar.")

st.divider()

# --- 4. SCANNER ---
st.subheader("🔍 Moneycontrol API SGB Scanner")
watch_list = ["SGBJUN31I", "SGBJUN27", "SGBMAY26", "SGBSEP31II"]
results = []

if live_spot > 0:
    st.write(f"*Calculated against Live Gold Spot: **₹{live_spot:,.2f} / gram***")
    for sgb in watch_list:
        price = get_mc_sgb_offer(sgb)
        if price > 0:  # <-- Fixed: Added the colon here
            disc = ((live_spot - price) / live_spot) * 100
            results.append({
                "Series": sgb, 
                "Live Offer Rate": f"₹{price:,.2f}", 
                "True Discount": f"{disc:.2f}%"
            })

    if results:
        st.table(pd.DataFrame(results))
    else:
        st.warning("⚠️ No data available from API.")
else:
    st.error("⚠️ Could not fetch Live Gold Spot.")
