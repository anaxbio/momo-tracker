import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Gold Carry Pro", page_icon="🪙", layout="wide")

# --- 1. THE MARCH GUINEA SCRAPER (Targeting ~130,660) ---
@st.cache_data(ttl=600)
def get_live_guinea_march():
    """Scrapes the March 2026 Gold Guinea from Google Finance"""
    # This URL targets the March 2026 Gold Guinea specifically
    url = "https://www.google.com/finance/quote/GOLDGUINEAMAR:MCX"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        # Google's price class
        price_text = soup.find(class_="YMlKec fxKbKc").text
        return float(price_text.replace('₹', '').replace(',', ''))
    except:
        return 0.0

@st.cache_data(ttl=600)
def get_gold_spot():
    gold = yf.Ticker("GC=F").fast_info['last_price']
    usdinr = yf.Ticker("INR=X").fast_info['last_price']
    return (gold / 31.1035) * usdinr

# --- 2. SGB DATA (Your Working Version) ---
MC_MAP = {"SGBJUN31I": "SGB54", "SGBJUN27": "SGB15", "SGBMAY26": "SGB10"}

@st.cache_data(ttl=600)
def get_mc_sgb_offer(nse_symbol):
    mc_code = MC_MAP.get(nse_symbol)
    url = f"https://priceapi.moneycontrol.com/pricefeed/nse/equitycash/{mc_code}"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5).json()
        return float(res['data'].get('OPrice', 0.0))
    except: return 0.0

# --- 3. SIDEBAR & LOGIC ---
st.sidebar.header("⚙️ Portfolio Settings")
my_sgb_qty = st.sidebar.number_input("SGB Units", value=24)
my_sgb_cost = st.sidebar.number_input("SGB Buy Price", value=15906.67)

my_mcx_lots = st.sidebar.number_input("Guinea Lots", value=3)
my_mcx_entry = st.sidebar.number_input("Short Entry", value=131600.0)

# Fetching Live Data
live_spot = get_gold_spot()
live_guinea = get_live_guinea_march() # Targeting the 130k-131k range
live_sgb = get_mc_sgb_offer("SGBJUN31I")

# --- 4. DASHBOARD ---
st.title("🪙 Gold Guinea Carry Tracker")
st.caption(f"Status: Tracking March Expiry | Spot: ₹{live_spot:,.2f}")

if live_sgb > 0 and live_guinea > 0:
    sgb_pnl = (live_sgb - my_sgb_cost) * my_sgb_qty
    # SHORT P&L: (Sold At - Current Price) * Lots
    # If Entry 131600 and Current 130660, profit is +940 per lot.
    mcx_pnl = (my_mcx_entry - live_guinea) * my_mcx_lots
    total_net = sgb_pnl + mcx_pnl

    c1, c2, c3 = st.columns(3)
    c1.metric("SGB P&L", f"₹{sgb_pnl:,.0f}", f"Rate: ₹{live_sgb:,.0f}")
    c2.metric("MCX P&L (Short)", f"₹{mcx_pnl:,.0f}", f"Rate: ₹{live_guinea:,.0f}", delta_color="inverse")
    c3.metric("NET PROFIT", f"₹{total_net:,.0f}", "Combined")
else:
    st.error("Market data fetch failed. Using last cached prices.")
