import os
import sys
import json
import requests

def load_dotenv(path=".env"):
    try:
        from dotenv import load_dotenv as _load
        _load(path)
        return
    except ImportError:
        pass
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ[key] = value

def main():
    load_dotenv()
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    paper_endpoint = os.getenv("ALPACA_PAPER_ENDPOINT", "https://paper-api.alpaca.markets/v2")
    
    if not api_key or not secret_key:
        print("Error: Missing ALPACA_API_KEY or ALPACA_SECRET_KEY.")
        sys.exit(1)
    
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key
    }
    
    data_base = "https://data.alpaca.markets/v2"
    trade_url = f"{data_base}/stocks/AAPL/trades/latest"
    
    try:
        resp = requests.get(trade_url, headers=headers, timeout=10)
        resp.raise_for_status()
        price = float(resp.json()["trade"]["p"])
        print(f"Latest AAPL trade price: ${price:.2f}")
    except Exception as e:
        print(f"Error fetching latest AAPL trade: {e}")
        sys.exit(1)
    
    if price < 280:
        print(f"Price ${price:.2f} < $280. Checking buying power...")
        account_url = f"{paper_endpoint}/account"
        buying_power = 0.0
        try:
            resp = requests.get(account_url, headers=headers, timeout=10)
            resp.raise_for_status()
            buying_power = float(resp.json().get("buying_power", 0))
            print(f"Buying power: ${buying_power:.2f}")
        except Exception as e:
            print(f"Error fetching account: {e}")
        
        if buying_power >= price:
            print("Submitting buy order for 1 share...")
            order = {"symbol": "AAPL", "qty": "1", "side": "buy", "type": "market", "time_in_force": "day"}
            order_url = f"{paper_endpoint}/orders"
            resp = None
            try:
                resp = requests.post(order_url, json=order, headers=headers, timeout=10)
                resp.raise_for_status()
                print("Buy order submitted:", json.dumps(resp.json(), indent=2))
            except Exception as e:
                print(f"Error submitting buy order: {e}")
                if resp: print("Response:", resp.text)
        else:
            print(f"Insufficient buying power (${buying_power:.2f} < ${price:.2f}). Skip buy.")
    
    elif price > 290:
        print(f"Price ${price:.2f} > $290. Checking AAPL position...")
        position_url = f"{paper_endpoint}/positions/AAPL"
        qty = 0.0
        try:
            resp = requests.get(position_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                qty = float(resp.json().get("qty", 0))
                print(f"Shares held: {qty}")
            elif resp.status_code == 404:
                print("No AAPL position.")
            else:
                resp.raise_for_status()
        except Exception as e:
            print(f"Error fetching position: {e}")
        
        if qty >= 1:
            print("Submitting sell order for 1 share...")
            order = {"symbol": "AAPL", "qty": "1", "side": "sell", "type": "market", "time_in_force": "day"}
            order_url = f"{paper_endpoint}/orders"
            resp = None
            try:
                resp = requests.post(order_url, json=order, headers=headers, timeout=10)
                resp.raise_for_status()
                print("Sell order submitted:", json.dumps(resp.json(), indent=2))
            except Exception as e:
                print(f"Error submitting sell order: {e}")
                if resp: print("Response:", resp.text)
        else:
            print(f"Insufficient shares (have {qty}). Skip sell.")
    
    else:
        print(f"Price ${price:.2f} is between $280 and $290 inclusive. No action taken.")

if __name__ == "__main__":
    main()