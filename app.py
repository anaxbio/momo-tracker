import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.set_page_config(page_title="Gold Carry Pro", page_icon="🪙", layout="wide")

# --- 1. SGB MAPPING ---
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
    except Exception:
        return 0.0

@st.cache_data(ttl=600)
def get_mc_sgb_offer(nse_symbol):
    mc_code = MC_MAP.get(nse_symbol)
    if not mc_code:
        return 0.0
    url = f"https://priceapi.moneycontrol.com/pricefeed/nse/equitycash/{mc_code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5).json()
        offer = float(res['data'].get('OPrice', 0.0))
        ltp = float(res['data'].get('pricecurrent', 0.0))
        return offer if offer > 0 else ltp
    except Exception:
        return 0.0

# --- 2. THE RESILIENT MCX ENGINE ---
@st.cache_data(ttl=600)
def get_mc_guinea_price():
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # Attempt 1: The Moneycontrol MCX
