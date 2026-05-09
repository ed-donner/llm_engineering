#!/usr/bin/env python3

import os
import sys
import requests
from dotenv import load_dotenv

def main():
    load_dotenv()

    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    paper_endpoint = os.getenv("ALPACA_PAPER_ENDPOINT", "https://paper-api.alpaca.markets/v2")

    if not api_key or not secret_key:
        print("Error: ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in .env")
        sys.exit(1)

    trading_base = paper_endpoint.rstrip('/')
    data_base = "https://data.alpaca.markets/v2"

    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key,
        "Content-Type": "application/json"
    }

    # Fetch latest AAPL trade price
    try:
        resp = requests.get(f"{data_base}/stocks/AAPL/trades/latest", headers=headers, timeout=10)
        resp.raise_for_status()
        latest_trade = resp.json().get("trade")
        if not latest_trade:
            print("No AAPL trade data available.")
            sys.exit(1)
        price = float(latest_trade["p"])
        print(f"Latest AAPL trade price: ${price:.2f}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching latest trade: {e}")
        sys.exit(1)

    # Decision
    if price < 280:
        action = "BUY"
    elif price > 290:
        action = "SELL"
    else:
        action = "HOLD"

    print(f"Action decision: {action}")

    if action == "BUY":
        try:
            resp = requests.get(f"{trading_base}/account", headers=headers, timeout=10)
            resp.raise_for_status()
            account = resp.json()
            buying_power = float(account["buying_power"])
            print(f"Account buying power: ${buying_power:.2f}")

            if buying_power < price:
                print(f"Insufficient buying power to buy 1 share (need ${price:.2f}, have ${buying_power:.2f}). Skipping order.")
            else:
                order_payload = {
                    "symbol": "AAPL",
                    "qty": "1",
                    "side": "buy",
                    "type": "market",
                    "time_in_force": "day"
                }
                try:
                    order_resp = requests.post(f"{trading_base}/orders", headers=headers, json=order_payload, timeout=10)
                    order_resp.raise_for_status()
                    order_data = order_resp.json()
                    print(f"Order submitted successfully: {order_data}")
                except requests.exceptions.RequestException as e:
                    print(f"Error submitting buy order: {e}")
                    if hasattr(e, 'response') and e.response is not None:
                        print(f"Response: {e.response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching account: {e}")

    elif action == "SELL":
        try:
            resp = requests.get(f"{trading_base}/positions/AAPL", headers=headers, timeout=10)
            if resp.status_code == 404:
                print("No AAPL position found (0 shares held).")
                qty_held = 0
            else:
                resp.raise_for_status()
                position = resp.json()
                qty_held = float(position["qty"])
                print(f"AAPL position quantity held: {qty_held}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching AAPL position: {e}")
            sys.exit(0)

        if qty_held >= 1:
            order_payload = {
                "symbol": "AAPL",
                "qty": "1",
                "side": "sell",
                "type": "market",
                "time_in_force": "day"
            }
            try:
                order_resp = requests.post(f"{trading_base}/orders", headers=headers, json=order_payload, timeout=10)
                order_resp.raise_for_status()
                order_data = order_resp.json()
                print(f"Order submitted successfully: {order_data}")
            except requests.exceptions.RequestException as e:
                print(f"Error submitting sell order: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Response: {e.response.text}")
        else:
            print(f"Position quantity ({qty_held}) less than 1, cannot sell 1 share. Skipping.")

    else:
        print(f"Price ${price:.2f} is within 280-290 range. No action taken.")


if __name__ == "__main__":
    main()