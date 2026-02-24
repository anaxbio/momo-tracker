import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- CONFIGURATION & UNIVERSE ---
# The universe of ETFs to scan. (Add or remove as needed)
ETF_UNIVERSE = [
    "SILVERIETF.NS", "QGOLDHALF.NS", "HDFCPSUBK.NS", "METALIETF.NS", 
    "NIFTYBEES.NS", "BANKBEES.NS", "MON100.NS", "LIQUIDBEES.NS", 
    "PHARMABEES.NS", "ITBEES.NS", "CPSEETF.NS", "MID150BEES.NS"
]

# Your current 10-stock EP + Stage 2 Watchlist/Portfolio
EP_STAGE2_STOCKS = [
    "DEEDEV.NS", "KRN.NS", "AEGISLOG.NS", # Your current holdings
    "ZOMATO.NS", "SUZLON.NS", "IRFC.NS", "RVNL.NS", "TATACHEM.NS" # Fill out to 10 slots
]

BASE_CAPITAL = 200000  # Starting portfolio base

st.set_page_config(page_title="Momo Command Center", page_icon="📈", layout="wide")

@st.cache_data(ttl=3600)
def fetch_data(tickers, period="1y"):
    df = yf.download(tickers, period=period, group_by='ticker')
    return df

st.title("📈 Momentum Command Center")
tab1, tab2, tab3 = st.tabs(["Top 4 ETF Selection", "Adaptive Allocation (Top 2)", "EP + Stage 2 Tracker"])

# Fetch global data
etf_data = fetch_data(ETF_UNIVERSE, period="1y")

# --- TAB 1: TOP 4 ETF MOMENTUM (SELECTION) ---
with tab1:
    st.header("1. Top 4 ETF Selection (Pure Momentum Score)")
    st.info("Rule: Rank entire ETF universe based on Equal Weight Momentum: (3M 25% + 6M 25% + 9M 25% + 12M 25%)")
    
    results = []
    for t in ETF_UNIVERSE:
        try:
            hist = etf_data[t]['Close'].dropna()
            if len(hist) > 250:
                p_now = hist.iloc[-1]
                # Calculate returns approx 63, 126, 189, 252 trading days
                r3 = (p_now / hist.iloc[-63]) - 1
                r6 = (p_now / hist.iloc[-126]) - 1
                r9 = (p_now / hist.iloc[-189]) - 1
                r12 = (p_now / hist.iloc[-252]) - 1
                
                # Equal Weight Pure Momo Score (25% each)
                momo_score = (r3 * 0.25) + (r6 * 0.25) + (r9 * 0.25) + (r12 * 0.25)
                results.append({"ETF": t, "Price": p_now, "Score": momo_score})
        except Exception:
            pass
            
    if results:
        momo_df = pd.DataFrame(results).sort_values(by="Score", ascending=False).reset_index(drop=True)
        # We still show the Top 4 for tracking, but only pass Top 2 to the Adaptive tab
        top_2_etfs = momo_df.head(2)["ETF"].tolist()
        
        st.write("### Current ETF Ranking:")
        st.dataframe(momo_df.head(10).style.format({"Price": "₹{:.2f}", "Score": "{:.2%}"}).background_gradient(subset=['Score'], cmap='Greens'))

# --- TAB 2: ADAPTIVE MOMENTUM (RISK WEIGHTING - TOP 2 ONLY) ---
with tab2:
    st.header("2. Adaptive Allocation (Top 2 Inverse Volatility)")
    st.info(f"Rule: Allocate ₹{BASE_CAPITAL:,.0f} across strictly the **Top 2** momentum ETFs based on 3-Month Inverse Volatility.")
    
    if 'top_2_etfs' in locals() and len(top_2_etfs) == 2:
        # Get 3-month daily returns for ONLY the Top 2
        close_prices = pd.DataFrame({t: etf_data[t]['Close'] for t in top_2_etfs}).dropna().tail(63) 
        daily_returns = close_prices.pct_change().dropna()
        
        # Calculate Inverse Volatility
        vol_3m = daily_returns.std() * np.sqrt(252)
        inv_vol = 1 / vol_3m
        weights = inv_vol / inv_vol.sum()
        
        # Calculate capital split
        alloc_df = pd.DataFrame({
            "ETF": weights.index,
            "Current Price": close_prices.iloc[-1].values,
            "Target Weight": weights.values,
            "Capital Allocation": weights.values * BASE_CAPITAL
        }).sort_values(by="Target Weight", ascending=False)
        
        # Calculate exact units to buy
        alloc_df["Units to Buy"] = (alloc_df["Capital Allocation"] / alloc_df["Current Price"]).astype(int)
        
        st.write("### Required Execution (Top 2 Assets Only):")
        st.dataframe(alloc_df.style.format({
            "Target Weight": "{:.1%}",
            "Current Price": "₹{:.2f}",
            "Capital Allocation": "₹{:,.2f}"
        }))
        st.warning("Rebalance Frequency: Last Wednesday of the month (or Friday).")

# --- TAB 3: EP MOMO + STAGE 2 (STOCK TRACKER) ---
with tab3:
    st.header("3. High-Velocity 10-Stock Portfolio")
    st.info("Rules: Requires Stage 2 setup. Hard Stop Loss at -5% to -7%. Swap weakest link for new EP.")
    
    stock_data = fetch_data(EP_STAGE2_STOCKS, period="1y")
    stock_results = []
    
    for t in EP_STAGE2_STOCKS:
        try:
            hist = stock_data[t].dropna()
            if len(hist) > 200:
                p_now = hist['Close'].iloc[-1]
                sma50 = hist['Close'].rolling(50).mean().iloc[-1]
                sma200 = hist['Close'].rolling(200).mean().iloc[-1]
                ret_1m = (p_now / hist['Close'].iloc[-21]) - 1 # 1-month momentum to find weakest link
                
                stage_2 = (p_now > sma50) and (sma50 > sma200)
                status = "🟢 Stage 2 Confirmed" if stage_2 else "🔴 Lost Stage 2"
                
                stock_results.append({
                    "Stock": t,
                    "Price": p_now,
                    "Stage 2 Status": status,
                    "Dist from 50 DMA": (p_now / sma50) - 1,
                    "Recent 1M Momo": ret_1m
                })
        except Exception:
            pass

    if stock_results:
        st_df = pd.DataFrame(stock_results).sort_values(by="Recent 1M Momo", ascending=False).reset_index(drop=True)
        
        st.write("### Current 10-Slot Roster:")
        st.dataframe(st_df.style.format({
            "Price": "₹{:.2f}",
            "Dist from 50 DMA": "{:.2%}",
            "Recent 1M Momo": "{:.2%}"
        }).map(lambda x: 'color: red' if 'Lost' in str(x) else 'color: green', subset=['Stage 2 Status']))
        
        # Identify weakest link
        weakest = st_df.iloc[-1]
        st.error(f"**Swap Rule Alert:** {weakest['Stock']} is your weakest performer (1M Momo: {weakest['Recent 1M Momo']:.2%}). It is a candidate to swap for a new EP setup. Ensure strict 5-7% stop-loss.")
