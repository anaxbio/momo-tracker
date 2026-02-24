import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import time

st.set_page_config(page_title="Gold Carry Pro", page_icon="🪙", layout="wide")

# --- 1. DATA ENGINES ---
@st.cache_data(ttl=3600)
def get_gold_gram():
    gold = yf.Ticker("GC=F").fast_info['last_price']
    usdinr = yf.Ticker("INR=X").fast_info['last_price']
    return (gold / 31.1035) * usdinr

@st.cache_data(ttl=3600)
def get_true_sgb_depth(symbol):
    home_url = "https://www.nseindia.com"
    api_url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        session = requests.Session()
        session.get(home_url, headers=headers, timeout=5)
        response = session.get(api_url, headers=headers, timeout=5)
        data = response.json()
        
        best_bid = data['marketDeptOrderBook']['bid'][0]['price']
        best_offer = data['marketDeptOrderBook']['ask'][0]['price']
        qty = data['marketDeptOrderBook']['ask'][0]['quantity']
        return best_bid, best_offer, qty
    except:
        return None, None, None

# Fetch Spot
try:
    live_spot = get_gold_gram()
except:
    live_spot = 16080.0

# --- 2. SIDEBAR (Your Locked-in Trades) ---
st.sidebar.header("⚙️ My Portfolio Settings")
my_qty = st.sidebar.number_input("Units Held", value=24)
my_sgb_cost = st.sidebar.number_input("SGB Avg Buy Price", value=15906.67)
my_guinea_sell_lot = st.sidebar.number_input("Guinea Short Lot Price", value=131600.0)

# We use your SGBJUN31I scraper data to power your P&L
my_bid, my_offer, my_qty_avail = get_true_sgb_depth("SGBJUN31I")
# If scraper fails, default to a safe estimate
active_sgb_price = my_bid if my_bid else 15920.0 

guinea_gram_sell = my_guinea_sell_lot / 8
live_guinea_gram = (live_spot * 1.025) 

# --- 3. MAIN DASHBOARD ---
st.title("🪙 Gold Guinea Carry Tracker (Pro)")

sgb_pnl = (active_sgb_price - my_sgb_cost) * my_qty
mcx_pnl = (guinea_gram_sell - live_guinea_gram) * my_qty
total_net = sgb_pnl + mcx_pnl

c1, c2, c3 = st.columns(3)
# We use the 'Bid' here because if you had to sell your SGBs right now, that's what you'd get
c1.metric("SGB P&L (At Bid)", f"₹{sgb_pnl:,.0f}", delta=f"Price: {active_sgb_price}")
c2.metric("MCX P&L", f"₹{mcx_pnl:,.0f}", delta_color="inverse")
c3.metric("NET PROFIT", f"₹{total_net:,.0f}", "Pure Carry")

st.divider()

# --- 4. TRUE DEPTH SCANNER ---
st.subheader("🔍 True Market Depth Scanner (Live Offers)")
watch_list = ["SGBJUN31I", "SGBJUN27", "SGBMAY26"]
results = []

for sgb in watch_list:
    bid, offer, qty = get_true_sgb_depth(sgb)
    if offer:
        disc = ((live_spot - offer) / live_spot) * 100
        results.append({
            "Series": sgb, 
            "Best Offer (You Pay)": f"₹{offer}", 
            "Available Qty": qty,
            "True Discount": f"{disc:.2f}%"
        })

if results:
    st.table(pd.DataFrame(results))
else:
    st.error("⚠️ NSE firewall blocked the request this hour. We will try again automatically later.")
