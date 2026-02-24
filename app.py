import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Adaptive Momentum", layout="wide")
st.title("🧭 Adaptive Momentum (Top 2)")

# --- 1. SETTINGS & UNIVERSE ---
# The specific 4-asset macro universe for Adaptive Momentum
UNIVERSE = ["NIFTYBEES.NS", "JUNIORBEES.NS", "GOLDBEES.NS", "LIQUIDBEES.NS"]

# Let you change capital on the fly
base_capital = st.number_input("Portfolio Base Capital (₹)", value=200000, step=10000)

st.info("Rule: Rank the 4 macro assets by 6-Month Momentum. Pick the Top 2. Weight them using 3-Month Inverse Volatility.")

# --- 2. FETCH DATA ---
@st.cache_data(ttl=3600)
def get_clean_data(tickers):
    # Download 1 year of data
    df = yf.download(tickers, period="1y")['Close']
    # Forward-fill missing days (holidays/glitches) so it doesn't break the math
    df = df.ffill().dropna()
    return df

with st.spinner("Fetching market data..."):
    df = get_clean_data(UNIVERSE)

if not df.empty:
    # --- 3. SELECT TOP 2 BY MOMENTUM (6 Months / ~126 trading days) ---
    # Calculate return from 126 days ago to today
    momo_6m = (df.iloc[-1] / df.iloc[-126]) - 1
    
    # Sort and pick the top 2
    top_2_series = momo_6m.sort_values(ascending=False).head(2)
    top_2_tickers = top_2_series.index.tolist()
    
    st.write("### 🏆 Step 1: Momentum Winners")
    st.write(f"The top 2 performing assets over the last 6 months are **{top_2_tickers[0]}** and **{top_2_tickers[1]}**.")
    
    # --- 4. CALCULATE INVERSE VOLATILITY (3 Months / ~63 trading days) ---
    # Slice the dataframe to just the Top 2 assets for the last 63 days
    df_top2 = df[top_2_tickers].tail(63)
    daily_returns = df_top2.pct_change().dropna()
    
    # Calculate annualized volatility
    volatility = daily_returns.std() * np.sqrt(252)
    
    # Calculate Inverse Volatility weights
    inv_vol = 1 / volatility
    weights = inv_vol / inv_vol.sum()
    
    # --- 5. BUILD THE EXECUTION TABLE ---
    current_prices = df_top2.iloc[-1]
    
    alloc_df = pd.DataFrame({
        "Asset": weights.index,
        "Current Price": current_prices.values,
        "6M Momentum": top_2_series.values,
        "Annual Volatility": volatility.values,
        "Target Weight": weights.values,
        "Capital Allocation": weights.values * base_capital
    }).sort_values(by="Target Weight", ascending=False)
    
    # Calculate whole units to buy
    alloc_df["Units to Buy"] = np.floor(alloc_df["Capital Allocation"] / alloc_df["Current Price"]).astype(int)
    
    st.write("### ⚖️ Step 2: Inverse Volatility Execution")
    st.dataframe(
        alloc_df.style.format({
            "Current Price": "₹{:.2f}",
            "6M Momentum": "{:.2%}",
            "Annual Volatility": "{:.2%}",
            "Target Weight": "{:.1%}",
            "Capital Allocation": "₹{:,.2f}"
        }),
        hide_index=True
    )
else:
    st.error("Failed to fetch data from Yahoo Finance. Please refresh the page.")
        st.error(f"**Swap Rule Alert:** {weakest['Stock']} is your weakest performer (1M Momo: {weakest['Recent 1M Momo']:.2%}). It is a candidate to swap for a new EP setup. Ensure strict 5-7% stop-loss.")
