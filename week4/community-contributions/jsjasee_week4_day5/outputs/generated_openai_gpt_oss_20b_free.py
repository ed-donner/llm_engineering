import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_PAPER_ENDPOINT = os.getenv("ALPACA_PAPER_ENDPOINT", "https://paper-api.alpaca.markets/v2")

def print_error(msg):
    print(f"ERROR: {msg}")

def exit_if_missing_creds():
    missing = []
    for name, val in [("OPENROUTER_API_KEY", OPENROUTER_API_KEY),
                      ("ALPACA_API_KEY", ALPACA_API_KEY),
                      ("ALPACA_SECRET_KEY", ALPACA_SECRET_KEY),
                      ("ALPACA_PAPER_ENDPOINT", ALPACA_PAPER_ENDPOINT)]:
        if not val:
            missing.append(name)
    if missing:
        print_error(f"Missing credentials: {', '.join(missing)}")
        sys.exit(1)

def get_latest_aapl_trade():
    url = "https://api.alpaca.markets/v2/stocks/NYSE/AAPL/trades/latest"
    headers = {"APCA-API-KEY-ID": ALPACA_API_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        price = float(data["trade"]["price"])
        print(f"Latest AAPL trade price: {price}")
        return price
    except Exception as e:
        print_error(f"Failed to fetch latest AAPL trade: {e}")
        sys.exit(1)

def get_buying_power():
    url = f"{ALPACA_PAPER_ENDPOINT}/accounts"
    headers = {"APCA-API-KEY-ID": ALPACA_API_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return float(data["cash"])
    except Exception as e:
        print_error(f"Failed to fetch buying power: {e}")
        return None

def get_aapl_position():
    url = f"{ALPACA_PAPER_ENDPOINT}/positions/AAPL"
    headers = {"APCA-API-KEY-ID": ALPACA_API_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 404:
            return 0
        resp.raise_for_status()
        data = resp.json()
        return int(float(data["qty"]))
    except Exception as e:
        print_error(f"Failed to fetch AAPL position: {e}")
        return None

def submit_order(side, qty=1, price=None):
    url = f"{ALPACA_PAPER_ENDPOINT}/orders"
    headers = {"APCA-API-KEY-ID": ALPACA_API_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY, "Content-Type": "application/json"}
    payload = {
        "symbol": "AAPL",
        "qty": qty,
        "side": side,
        "type": "market",
        "time_in_force": "day"
    }
    if price:
        payload["price"] = price
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        print("Order submitted successfully.")
        print("Order response:", data)
    except Exception as e:
        print_error(f"Order submission failed: {e}")

def main():
    exit_if_missing_creds()
    price = get_latest_aapl_trade()

    if price < 280:
        buying_power = get_buying_power()
        if buying_power is None:
            print_error("Could not determine buying power; skipping order.")
            return
        if buying_power >= price:
            print(f"Buying power sufficient (${buying_power:.2f} >= ${price:.2f}). Placing BUY order for 1 share.")
            submit_order("buy")
        else:
            print(f"Insufficient buying power (${buying_power:.2f}) to buy at ${price:.2f}. Skipping.")
    elif price > 290:
        position_qty = get_aapl_position()
        if position_qty is None:
            print_error("Could not determine AAPL position; skipping order.")
            return
        if position_qty >= 1:
            print(f"Holding {position_qty} shares. Placing SELL order for 1 share.")
            submit_order("sell")
        else:
            print(f"No shares to sell (position {position_qty}). Skipping.")
    else:
        print(f"Price ${price:.2f} is between 280 and 290 inclusive. No action taken.")

if __name__ == "__main__":
    main()