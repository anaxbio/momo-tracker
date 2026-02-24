import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Gold Carry Pro", page_icon="🪙", layout="wide")

# --- 1. YAHOO FINANCE DATA ENGINES ---
@st.cache_data(ttl=3600)
def get_gold_gram():
    # Global Gold to INR conversion
    gold = yf.Ticker("GC=F").fast_info['last_price']
    usdinr = yf.Ticker("INR=X").fast_info['last_price']
    return (gold / 31.1035) * usdinr

@st.cache_data(ttl=3600)
def get_yahoo_offer(symbol):
    """Pulls the actual Ask (Offer) price from Yahoo Finance"""
    try:
        # Yahoo requires '.NS' for NSE stocks
        info = yf.Ticker(f"{symbol}.NS").info
        
        # Grab the Bid and Ask
        bid = info.get('bid')
        offer = info.get('ask')
        
        # Failsafe: If market is closed, Yahoo sometimes shows 0 for Ask. 
        # In that case, we fall back to the Last Traded Price (currentPrice)
        if not offer or offer == 0:
            offer = info.get('currentPrice')
            
        return offer
    except:
        return None

# Fetch Spot Gold
try:
    live_spot = get_gold_gram()
except:
    live_spot = 16080.0

# --- 2. SIDEBAR (Your Locked-in Trades) ---
st.sidebar.header("⚙️ My Portfolio Settings")
my_qty = st.sidebar.number_input("Units Held", value=24)
my_sgb_cost = st.sidebar.number_input("SGB Avg Buy Price", value=15906.67)
my_guinea_sell_lot = st.sidebar.number_input("Guinea Short Lot Price", value=131600.0)

# Fetch your specific SGB Live Offer
live_sgb_offer = get_yahoo_offer("SGBJUN31I")
if not live_sgb_offer:
    live_sgb_offer = 15920.0 # Fallback if Yahoo is down

guinea_gram_sell = my_guinea_sell_lot / 8
live_guinea_gram = (live_spot * 1.025) 

# --- 3. MAIN DASHBOARD ---
st.title("🪙 Gold Guinea Carry Tracker")

sgb_pnl = (live_sgb_offer - my_sgb_cost) * my_qty
mcx_pnl = (guinea_gram_sell - live_guinea_gram) * my_qty
total_net = sgb_pnl + mcx_pnl

c1, c2, c3 = st.columns(3)
c1.metric("SGB P&L (At Offer)", f"₹{sgb_pnl:,.0f}", delta=f"Price: {live_sgb_offer}")
c2.metric("MCX P&L", f"₹{mcx_pnl:,.0f}", delta_color="inverse")
c3.metric("NET PROFIT", f"₹{total_net:,.0f}", "Pure Carry")

st.divider()

# --- 4. YAHOO MARKET SCANNER ---
st.subheader("🔍 Live SGB Scanner (Yahoo Finance)")
watch_list = ["SGBJUN31I", "SGBJUN27", "SGBMAY26"]
results = []

for sgb in watch_list:
    offer = get_yahoo_offer(sgb)
    if offer:
        disc = ((live_spot - offer) / live_spot) * 100
        results.append({
            "Series": sgb, 
            "Best Offer (Ask)": f"₹{offer:,.0f}", 
            "Live Discount": f"{disc:.2f}%"
        })

if results:
    st.table(pd.DataFrame(results))
else:
    st.error("Yahoo Finance data is temporarily unavailable.")
