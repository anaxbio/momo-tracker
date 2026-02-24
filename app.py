@st.cache_data(ttl=3600)
def get_mc_sgb_offer(nse_symbol):
    mc_code = MC_MAP.get(nse_symbol)
    if not mc_code:
        return 0.0
        
    url = f"https://priceapi.moneycontrol.com/pricefeed/nse/equitycash/{mc_code}"
    
    # THE FIX: The "Fake ID" so Moneycontrol doesn't block us
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # Notice we added headers=headers here
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        
        # Extract the exact Offer/Ask Price
        offer = float(data['data'].get('OPrice', 0.0))
        ltp = float(data['data'].get('pricecurrent', 0.0))
        
        # If the market is closed/no sellers, fallback to the Last Traded Price
        return offer if offer > 0 else ltp
    except:
        return 0.0
