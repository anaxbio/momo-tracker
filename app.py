import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Gold Carry Pro", page_icon="🪙", layout="wide")

# --- 1. DATA SCRAPERS (No Fake Fallbacks) ---
@st.cache_data(ttl=3600)
def get_gold_spot():
    try:
        gold = yf.Ticker("GC=F").fast_info['last_price']
        usdinr = yf.Ticker("INR=X").fast_info['last_price']
        return (gold / 31.1035) * usdinr
    except:
        return 0.0  # Returns 0 if it fails, so we know it's broken

@st.cache_data(ttl=3600)
def scrape_google_finance(ticker):
    url = f"https://www.google.com/finance/quote/{ticker}:NSE"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        price_text = soup.find(class_="YMlKec fxKbKc").text
        return float(price_text.replace('₹', '').replace(',', ''))
    except:
        return 0.0  # Returns 0 if scraper gets blocked

live_spot = get_gold_spot()

# --- 2. SIDEBAR (Clean Inputs) ---
st.sidebar.header("⚙️ My Portfolio Settings")

# Defaulting everything to 0 so no fake profits are shown
my_sgb_qty = st.sidebar.number_input("SGB Units Bought", value=0, step=8)
my_sgb_cost = st.sidebar.number_input("SGB Avg Buy Price", value=0.0, format="%.2f")

my_mcx_lots = st.sidebar.number_input("Guinea Lots Sold", value=0, step=1)
my_guinea_sell_lot = st.sidebar.number_input("Guinea Short Avg (Entry)", value=0.0, format="%.2f")

st.sidebar.divider()
st.sidebar.header("📈 Live MCX Price")
live_guinea_lot_ltp = st.sidebar.number_input("Live Guinea Lot LTP", value=0.0, format="%.2f")

# Fetch Scraped SGB Price
scraped_sgb = scrape_google_finance("SGBJUN31I")

st.sidebar.header("🔄 Manual SGB Override")
st.sidebar.caption("If the Google scraper fails (shows ₹0), type the live price here:")
manual_sgb_price = st.sidebar.number_input("Override SGB Price", value=0.0, format="%.2f")

# Logic: Use manual input if provided, otherwise use the scraped price
live_sgb_price = manual_sgb_price if manual_sgb_price > 0 else scraped_sgb

# --- 3. MAIN DASHBOARD ---
st.title("🪙 Gold Guinea Carry Tracker")

# Only run math if the user has actually put in their portfolio numbers
if my_sgb_qty > 0 and my_mcx_lots > 0 and live_sgb_price > 0 and live_guinea_lot_ltp > 0:
    sgb_pnl = (live_sgb_price - my_sgb_cost) * my_sgb_qty
    mcx_pnl = (my_guinea_sell_lot - live_guinea_lot_ltp) * my_mcx_lots
    total_net = sgb_pnl + mcx_pnl

    c1, c2, c3 = st.columns(3)
    c1.metric("SGB P&L", f"₹{sgb_pnl:,.2f}", delta=f"LTP: ₹{live_sgb_price:,.2f}")
    c2.metric("MCX P&L", f"₹{mcx_pnl:,.2f}", delta=f"Lot: ₹{live_guinea_lot_ltp:,.2f}", delta_color="inverse")
    c3.metric("NET PROFIT", f"₹{total_net:,.2f}", "Locked Carry")
else:
    st.info("👈 Please enter your portfolio quantities, entry prices, and the live MCX price in the sidebar to calculate your P&L.")

st.divider()

# --- 4. LIVE SCANNER ---
st.subheader("🔍 Google Finance SGB Scanner")
watch_list = ["SGBJUN31I", "SGBJUN27", "SGBMAY26"]
results = []

if live_spot > 0:
    st.write(f"*Calculated against Live Gold Spot: **₹{live_spot:,.2f} / gram***")
    for sgb in watch_list:
        price = scrape_google_finance(sgb)
        if price > 0:
            disc = ((live_spot - price) / live_spot) * 100
            results.append({
                "Series": sgb, 
                "Live Google Price": f"₹{price:,.2f}", 
                "Est. Discount": f"{disc:.2f}%"
            })

    if results:
        st.table(pd.DataFrame(results))
    else:
        st.warning("⚠️ Google Finance scraper returned no data. Check market hours or manually verify prices.")
else:
    st.error("⚠️ Could not fetch Live Gold Spot. Yahoo Finance might be blocked.")
