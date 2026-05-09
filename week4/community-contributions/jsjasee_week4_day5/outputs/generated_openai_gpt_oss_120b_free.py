import os
import sys
import requests
from dotenv import load_dotenv

def fetch_latest_price(headers):
    url = "https://data.alpaca.markets/v2/stocks/AAPL/trades/latest"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            trade = data.get("trade")
            if isinstance(trade, dict) and "p" in trade:
                return float(trade["p"])
            if "price" in data:
                return float(data["price"])
        print("Error: Unexpected latest trade response format.")
    except requests.RequestException as e:
        print(f"Error fetching latest price: {e}")
    return None

def fetch_account(headers, base):
    url = f"{base.rstrip('/')}/account"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"Error fetching account info: {e}")
    return None

def fetch_position(headers, base):
    url = f"{base.rstrip('/')}/positions/AAPL"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"Error fetching position: {e}")
    return None

def place_order(headers, base, side):
    url = f"{base.rstrip('/')}/orders"
    order_data = {
        "symbol": "AAPL",
        "qty": 1,
        "side": side,
        "type": "market",
        "time_in_force": "gtc"
    }
    resp = None
    try:
        resp = requests.post(url, json=order_data, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        if resp is not None:
            try:
                err = resp.json()
                print(f"Order error response: {err}")
            except Exception:
                print(f"Order error: {resp.text}")
        else:
            print(f"Error placing order: {e}")
    return None

def main():
    load_dotenv()
    alpaca_api_key = os.getenv("ALPACA_API_KEY")
    alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")
    alpaca_paper_endpoint = os.getenv("ALPACA_PAPER_ENDPOINT")
    # OpenRouter key read for completeness
    os.getenv("OPENROUTER_API_KEY")

    missing = []
    if not alpaca_api_key:
        missing.append("ALPACA_API_KEY")
    if not alpaca_secret_key:
        missing.append("ALPACA_SECRET_KEY")
    if not alpaca_paper_endpoint:
        missing.append("ALPACA_PAPER_ENDPOINT")
    if missing:
        print(f"Missing environment variable(s): {', '.join(missing)}")
        sys.exit(1)

    headers = {
        "APCA-API-KEY-ID": alpaca_api_key,
        "APCA-API-SECRET-KEY": alpaca_secret_key
    }

    price = fetch_latest_price(headers)
    if price is None:
        sys.exit(1)
    print(f"Latest AAPL trade price: ${price:.2f}")

    if price < 280:
        print("Decision: BUY 1 share (price below $280)")
        account = fetch_account(headers, alpaca_paper_endpoint)
        if account is None:
            sys.exit(1)
        buying_power = float(account.get("buying_power", "0"))
        print(f"Buying power: ${buying_power:.2f}")
        if buying_power >= price:
            order = place_order(headers, alpaca_paper_endpoint, "buy")
            if order:
                print("Order placed successfully:")
                print(order)
            else:
                print("Order submission failed.")
        else:
            print(f"Insufficient buying power (${buying_power:.2f}) to purchase 1 share at ${price:.2f}")
    elif price > 290:
        print("Decision: SELL 1 share (price above $290)")
        position = fetch_position(headers, alpaca_paper_endpoint)
        if position is None:
            print("No AAPL position found. Skipping sell order.")
        else:
            qty = float(position.get("qty", "0"))
            print(f"Current AAPL position: {int(qty)} shares")
            if qty >= 1:
                order = place_order(headers, alpaca_paper_endpoint, "sell")
                if order:
                    print("Order placed successfully:")
                    print(order)
                else:
                    print("Order submission failed.")
            else:
                print("Insufficient shares to sell (need at least 1). Skipping.")
    else:
        print("Decision: HOLD (price within $280-$290 inclusive). No action taken.")

if __name__ == "__main__":
    main()