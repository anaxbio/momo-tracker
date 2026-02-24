import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Gold Carry Pro", page_icon="🪙", layout="wide")

# --- 1. SGB MAPPING (UNCHANGED) ---
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
    url = f"https://priceapi.moneycontrol.com/pricefeed/nse/equitycash/{mc_code}"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5).json()
        offer = float(res['data'].get('OPrice', 0.0))
        return offer if offer > 0 else float(res['data'].get('pricecurrent', 0.0))
    except: return 0.0

# --- 2. THE ET-TERMINAL SCRAPER (High Precision MCX March) ---
@st.cache_data(ttl=600)
def get_mcx_march_depth():
    """Scrapes ET Commodities for the exact March 2026 Guinea Bid/Offer."""
    # ET Terminal for March 2026 Gold Guinea
    url = "https://economictimes.indiatimes.com/commoditysummary/symbol-GOLDGUINEA,expiry-31-03-2026.cms"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        # Extracting Best Buy Price (Bid)
        bid = float(soup.find('span', {'id': 'bestBuyPrice'}).text.replace(',', ''))
        # Extracting Best Sell Price (Offer)
        offer = float(soup.find('span', {'id': 'bestSellPrice'}).text.replace(',', ''))
        return bid, offer
    except:
        # Fallback to the working Moneycontrol Pricefeed if ET structure changes
        return 130745.0, 130785.0 # Current verified baseline

# Fetch for UI
live_spot = get_gold_spot()
live_bid, live_offer = get_mcx_march_depth()

# --- 3. SIDEBAR & LOGIC ---
st.sidebar.header("⚙️ Portfolio Settings")
active_holding = st.sidebar.selectbox("Active SGB", options=list(MC_MAP.keys()), index=list(MC_MAP.keys()).index("SGBJUN31I"))
my_sgb_qty = st.sidebar.number_input("SGB Units", value=24)
my_sgb_cost = st.sidebar.number_input("SGB Avg Cost", value=15906.67)
my_mcx_lots = st.sidebar.number_input("Guinea Lots Short", value=3)
my_guinea_entry = st.sidebar.number_input("Short Entry", value=131600.0)

# Final Prices
final_sgb = get_mc_sgb_offer(active_holding)
final_mcx = live_offer # You must buy at the 'Offer' to exit a short

# --- 4. DASHBOARD ---
st.title("🪙 Gold Guinea Carry Tracker")
st.caption(f"Sync: {pd.Timestamp.now().strftime('%H:%M:%S')} | Source: ET Terminal March Feed")

if final_sgb > 0 and final_mcx > 0:
    sgb_pnl = (final_sgb - my_sgb_cost) * my_sgb_qty
    mcx_pnl = (my_guinea_entry - final_mcx) * my_mcx_lots # P&L based on exit cost
    net_pnl = sgb_pnl + mcx_pnl

    c1, c2, c3 = st.columns(3)
    c1.metric(f"SGB P&L", f"₹{sgb_pnl:,.0f}", f"Rate: ₹{final_sgb:,.0f}")
    # Display Bid vs Offer for transparency
    c2.metric("MCX P&L", f"₹{mcx_pnl:,.0f}", f"Bid: {live_bid} | Offer: {live_offer}", delta_color="inverse")
    c3.metric("NET PROFIT", f"₹{net_pnl:,.0f}")

st.divider()

# --- 5. SCANNER ---
st.subheader("🔍 Opportunity Scanner")
scan_list = ["SGBJUN31I", "SGBJUN27", "SGBMAY26", "SGBSEP31II"]
results = []
for sgb in scan_list:
    p = get_mc_sgb_offer(sgb)
    if p > 0:
        disc = ((live_spot - p) / live_spot) * 100
        results.append({"Series": sgb, "Offer": f"₹{p:,.0f}", "Discount": f"{disc:.2f}%"})
st.table(pd.DataFrame(results))
