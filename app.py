@st.cache_data(ttl=600)
def get_guinea_march_bid():
    """Hunts the MCX feed to dynamically lock onto the March Best Bid"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Scan the near (01), next (02), and far (03) month MCX contracts
    for code in ["MGG01", "MGG02", "MGG03"]:
        url = f"https://priceapi.moneycontrol.com/pricefeed/mcx/futures/{code}"
        try:
            res = requests.get(url, headers=headers, timeout=5).json()
            
            # Convert the data payload to a string to search for the expiry month
            data_str = str(res.get('data', {})).upper()
            
            # If this is the March contract, lock onto the Bid
            if 'MAR' in data_str:
                # 'buyprice' is the Best Bid on Moneycontrol. 
                # Fallback to LTP if the market is closed and the Bid goes to 0.0.
                bid = float(res['data'].get('buyprice', 0.0))
                return bid if bid > 0 else float(res['data'].get('pricecurrent', 0.0))
        except:
            continue
            
    return 0.0

# Call it like this in your main code:
# live_guinea_bid = get_guinea_march_bid()
