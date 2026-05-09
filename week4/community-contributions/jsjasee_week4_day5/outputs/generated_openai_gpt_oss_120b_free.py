import os
import sys
import json
import requests
from dotenv import load_dotenv

def load_credentials():
    load_dotenv()
    required_vars = ["OPENROUTER_API_KEY", "ALPACA_API_KEY", "ALPACA_SECRET_KEY", "ALPACA_PAPER_ENDPOINT"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    return {
        "openrouter": os.getenv("OPENROUTER_API_KEY"),
        "alpaca_key": os.getenv("ALPACA_API_KEY"),
        "alpaca_secret": os.getenv("ALPACA_SECRET_KEY"),
        "paper_endpoint": os.getenv("ALPACA_PAPER_ENDPOINT").rstrip("/")
    }

def get_latest_trade_price(symbol, key_id, secret_key):
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/trades/latest"
    headers = {
        "APCA-API-KEY-ID": key_id,
        "APCA-API-SECRET-KEY": secret_key
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        trade = payload.get("trade")
        if not trade or "p" not in trade:
            print("Unexpected response structure for latest trade.")
            return None
        return float(trade["p"])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching latest trade for {symbol}: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                print(e.response.json())
            except Exception:
                print(e.response.text)
        return None

def get_account_info(base_url, headers):
    try:
        resp = requests.get(f"{base_url}/account", headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving account info: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                print(e.response.json())
            except Exception:
                print(e.response.text)
        return None

def get_position(base_url, headers, symbol):
    try:
        resp = requests.get(f"{base_url}/positions/{symbol}", headers=headers, timeout=10)
        if resp.status_code == 404:
            return None  # No position found
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving position for {symbol}: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                print(e.response.json())
            except Exception:
                print(e.response.text)
        return None

def submit_order(base_url, headers, symbol, side, qty=1):
    order_payload = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": "market",
        "time_in_force": "gtc"
    }
    try:
        resp = requests.post(f"{base_url}/orders", json=order_payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error submitting {side} order: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                print("Order error response:", json.dumps(e.response.json(), indent=2))
            except Exception:
                print("Order error response:", e.response.text)
        return None

def main():
    creds = load_credentials()
    key_id = creds["alpaca_key"]
    secret_key = creds["alpaca_secret"]
    paper_base = creds["paper_endpoint"]
    symbol = "AAPL"
    BUY_THRESHOLD = 280.0
    SELL_THRESHOLD = 290.0

    auth_headers = {
        "APCA-API-KEY-ID": key_id,
        "APCA-API-SECRET-KEY": secret_key
    }

    # 1. Fetch latest price
    latest_price = get_latest_trade_price(symbol, key_id, secret_key)
    if latest_price is None:
        print("Failed to obtain latest price. Exiting.")
        sys.exit(1)
    print(f"Latest {symbol} trade price: ${latest_price:.2f}")

    # 2. Decision logic
    if latest_price < BUY_THRESHOLD:
        decision = "BUY"
        print(f"Decision: price (${latest_price:.2f}) below ${BUY_THRESHOLD} → attempt to BUY 1 share")
    elif latest_price > SELL_THRESHOLD:
        decision = "SELL"
        print(f"Decision: price (${latest_price:.2f}) above ${SELL_THRESHOLD} → attempt to SELL 1 share")
    else:
        decision = "HOLD"
        print(f"Decision: price (${latest_price:.2f}) within [{BUY_THRESHOLD}, {SELL_THRESHOLD}] → no action")
        print("Reason: price does not meet buy or sell thresholds.")
        return

    # 3. Execute based on decision
    if decision == "BUY":
        account = get_account_info(paper_base, auth_headers)
        if not account:
            print("Cannot retrieve account information. Skipping buy order.")
            return
        buying_power = float(account.get("buying_power", "0"))
        print(f"Account buying power: ${buying_power:.2f}")
        if buying_power < latest_price:
            print(f"Insufficient buying power (${buying_power:.2f}) to cover purchase of 1 share at ${latest_price:.2f}. Order not submitted.")
            return
        print("Precondition check passed: sufficient buying power.")
        order_resp = submit_order(paper_base, auth_headers, symbol, "buy")
        if order_resp:
            print("Buy order submitted. Response:")
            print(json.dumps(order_resp, indent=2))
        else:
            print("Buy order failed.")
    elif decision == "SELL":
        position = get_position(paper_base, auth_headers, symbol)
        if not position:
            print("No existing AAPL position. Cannot sell. Order not submitted.")
            return
        qty = float(position.get("qty", "0"))
        print(f"Current AAPL position quantity: {qty}")
        if qty < 1:
            print("Insufficient shares to sell 1 share. Order not submitted.")
            return
        print("Precondition check passed: sufficient shares to sell.")
        order_resp = submit_order(paper_base, auth_headers, symbol, "sell")
        if order_resp:
            print("Sell order submitted. Response:")
            print(json.dumps(order_resp, indent=2))
        else:
            print("Sell order failed.")

if __name__ == "__main__":
    main()