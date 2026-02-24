import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import timedelta

# --- CONFIGURATION ---
# Replace these with your actual NSE tickers. Suffix with '.NS' for Indian stocks/ETFs.
STRATEGIES = {
    "Adaptive Momentum": ["NIFTYBEES.NS", "BANKBEES.NS", "GOLDBEES.NS", "LIQUIDBEES.NS"],
    "EP Momo + Stage 2": ["ZOMATO.NS", "SUZLON.NS", "IRFC.NS", "RVNL.NS"], 
    "Top 4 ETF Momo": ["CPSEETF.NS", "MID150BEES.NS", "ITBEES.NS", "PHARMABEES.NS", "CONSUMBEES.NS"]
}

st.set_page_config(page_title="Momo Command Center", page_icon="📈", layout="wide")

@st.cache_data(ttl=3600) # Caches data for 1 hour to load faster
def fetch_data(tickers, period="1y"):
    df = yf.download(tickers, period=period, group_by='ticker')
    return df

st.title("📈 Momo Command Center")
tab1, tab2, tab3 = st.tabs(["Adaptive Momentum", "EP + Stage 2", "Top 4 ETF Momo"])

# --- TAB 1: ADAPTIVE MOMENTUM ---
with tab1:
    st.header("Adaptive Momentum (Inverse Volatility)")
    tickers = STRATEGIES["Adaptive Momentum"]
    data = fetch_data(tickers, period="1y")
    
    if len(tickers) > 1:
        close_prices = pd.DataFrame({t: data[t]['Close'] for t in tickers}).dropna()
        daily_returns = close_prices.pct_change().dropna()
        
        # Calculate Inverse Volatility (Annualized)
        annual_vol = daily_returns.std() * np.sqrt(252)
        inv_vol = 1 / annual_vol
        weights = inv_vol / inv_vol.sum()
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write("### Target Allocations")
            weight_df = pd.DataFrame({"Asset": weights.index, "Weight (%)": weights.values * 100})
            weight_df = weight_df.sort_values(by="Weight (%)", ascending=False)
            st.dataframe(weight_df.style.format({"Weight (%)": "{:.1f}%"}))
            
        with col2:
            st.info("💡 **Action:** Allocate capital heavily to the top 2 assets with the lowest volatility. Sell off the laggards.")
            
# --- TAB 2: EP MOMO + STAGE 2 ---
with tab2:
    st.header("Episodic Pivot + Stage 2 Tracker")
    tickers = STRATEGIES["EP Momo + Stage 2"]
    data = fetch_data(tickers, period="2y") # Need 2 years for a solid 200 DMA
    
    cols = st.columns(len(tickers))
    for i, t in enumerate(tickers):
        with cols[i % len(cols)]:
            try:
                hist = data[t].dropna()
                curr_price = hist['Close'].iloc[-1]
                sma200 = hist['Close'].rolling(200).mean().iloc[-1]
                sma50 = hist['Close'].rolling(50).mean().iloc[-1]
                
                # Volume check for "Episodic Pivot" (Today's vol > 3x the 20-day average)
                avg_vol_20 = hist['Volume'].rolling(20).mean().iloc[-2]
                curr_vol = hist['Volume'].iloc[-1]
                ep_triggered = curr_vol > (avg_vol_20 * 3)
                
                # Stage 2 Check: Price > 50 DMA > 200 DMA
                stage_2 = (curr_price > sma50) and (sma50 > sma200)
                
                status_color = "normal" if stage_2 else "off"
                delta_val = "In Stage 2" if stage_2 else "Lost Stage 2"
                
                st.metric(label=t, value=f"₹{curr_price:.2f}", delta=delta_val, delta_color=status_color)
                
                if ep_triggered and stage_2:
                    st.success("🟢 BUY SIGNAL: EP & Stage 2 Confirmed")
                elif stage_2:
                    st.warning("🟡 HOLD: In Stage 2, waiting for EP setup.")
                else:
                    st.error("🔴 SELL / AVOID: Below Moving Averages.")
            except Exception as e:
                st.write(f"Error loading {t}")

# --- TAB 3: TOP 4 ETF MOMENTUM ---
with tab3:
    st.header("Relative Strength Ranking (Multi-Timeframe)")
    tickers = STRATEGIES["Top 4 ETF Momo"]
    data = fetch_data(tickers, period="1y")
    
    results = []
    for t in tickers:
        try:
            hist = data[t]['Close'].dropna()
            if len(hist) > 250:
                p_now = hist.iloc[-1]
                # Calculate returns for 3, 6, 9, 12 months (approx 63, 126, 189, 252 trading days)
                r3 = (p_now / hist.iloc[-63]) - 1
                r6 = (p_now / hist.iloc[-126]) - 1
                r9 = (p_now / hist.iloc[-189]) - 1
                r12 = (p_now / hist.iloc[-252]) - 1
                
                # Weighted Average Momentum Score
                weighted_score = (r3 * 0.4) + (r6 * 0.3) + (r9 * 0.2) + (r12 * 0.1)
                
                results.append({
                    "ETF": t,
                    "Current Price": p_now,
                    "3M Ret": r3,
                    "6M Ret": r6,
                    "9M Ret": r9,
                    "12M Ret": r12,
                    "Weighted RS Score": weighted_score
                })
        except Exception:
            pass
            
    if results:
        rs_df = pd.DataFrame(results).sort_values(by="Weighted RS Score", ascending=False)
        st.write("### The Top 4 to hold are at the top of this list:")
        # Formatting for readability
        format_dict = {col: "{:.2%}" for col in ["3M Ret", "6M Ret", "9M Ret", "12M Ret", "Weighted RS Score"]}
        format_dict["Current Price"] = "₹{:.2f}"
        st.dataframe(rs_df.style.format(format_dict).background_gradient(subset=['Weighted RS Score'], cmap='Greens'))
