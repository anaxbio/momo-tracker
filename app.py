import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
import pandas as pd

🍌 Nano Banana Flash App
st.set_page_config(page_title="Nano Banana Flash", page_icon="🍌")
st.title("🍌 Nano Banana Portfolio Flash")

1. Connect to your Google Sheet
This fetches your data (2290 Gold / 1533 Nasdaq) from the sheet URL in Secrets
try:
conn = st.connection("gsheets", type=GSheetsConnection)
# Read the tab named 'holdings'
df = conn.read(worksheet="holdings", ttl="1m")

except Exception as e:
st.error("⚠️ Connection Error")
st.write("Please check: 1. Your Google Sheet Tab is named 'holdings'. 2. Your Secrets URL is correct.")
st.write(f"Technical details: {e}"
