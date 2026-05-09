import os
import sys
import requests
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file if present
    load_dotenv()

    # Read credentials
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    alpaca_api_key = os.getenv("ALPACA_API_KEY")
    alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")
    paper_endpoint = os.getenv("ALPACA_PAPER_ENDPOINT")

    # Validate all required variables
    required = {
        "OPENROUTER_API_KEY": openrouter_key,
        "ALPACA_API_KEY": alpaca_api_key,
        "ALPACA_SECRET_KEY": alpaca_secret_key,
        "ALPACA_PAPER_ENDPOINT": paper_endpoint,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"Missing credentials: {', '.join(missing)}")
        sys.exit(1)

    # Ensure we only use paper trading
    base_url = paper_endpoint.rstrip("/")
    if "paper-api" not in base_url:
        print("ERROR: Only paper trading is allowed. Aborting.")
        sys.exit(1)

    headers = {
        "APCA-API-KEY-ID": alpaca_api_key,
        "APCA-API-SECRET-KEY": alpaca_secret_key,
        "Content-Type": "application/json",
    }

    # Fetch latest AAPL trade price
    try:
        trade_resp = requests.get(f"{base_url}/stocks/AAPL/trades/latest", headers=headers)
        trade_resp.raise_for_status()
        trade_data = trade_resp.json()
        latest_price = float(trade_data["trade"]["p"])
        print(f"Latest AAPL trade price: ${latest_price:.2f}")
    except Exception as e:
        print(f"Error fetching latest trade price: {e}")
        sys.exit(1)

    # Determine action
    if latest_price < 280:
        action = "buy"
    elif latest_price > 290:
        action = "sell"
    else:
        action = "hold"
        print(f"Price ${latest_price:.2f} is between 280 and 290 inclusive. No action taken.")
        return

    print(f"Action determined: {action}")

    # Get account information
    try:
        account_resp = requests.get(f"{base_url}/account", headers=headers)
        account_resp.raise_for_status()
        account = account_resp.json()
        buying_power = float(account["buying_power"])
        print(f"Account buying power: ${buying_power:.2f}")
    except Exception as e:
        print(f"Error fetching account: {e}")
        sys.exit(1)

    if action == "buy":
        # Precondition: sufficient buying power
        if buying_power < latest_price:
            print(
                f"Precondition FAILED: Insufficient buying power. "
                f"Need ${latest_price:.2f}, but only have ${buying_power:.2f}."
            )
            print("No order placed.")
            return
        print("Precondition met: sufficient buying power for 1 share.")

        # Submit buy order
        order_payload = {
            "symbol": "AAPL",
            "qty": "1",
            "side": "buy",
            "type": "market",
            "time_in_force": "day",
        }
        try:
            order_resp = requests.post(f"{base_url}/orders", headers=headers, json=order_payload)
            order_resp.raise_for_status()
            order_data = order_resp.json()
            print("Order placed successfully:")
            print(order_data)
        except Exception as e:
            print(f"Failed to place buy order: {e}")
            if order_resp is not None:
                print(f"Response: {order_resp.text}")
            sys.exit(1)

    elif action == "sell":
        # Check existing position
        try:
            pos_resp = requests.get(f"{base_url}/positions/AAPL", headers=headers)
            pos_resp.raise_for_status()
            position = pos_resp.json()
            qty = int(float(position["qty"]))
            print(f"Current AAPL position: {qty} shares")
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print("Precondition FAILED: No AAPL position found (0 shares).")
            else:
                print(f"Error fetching position: {e}")
            print("No order placed.")
            return
        except Exception as e:
            print(f"Error fetching position: {e}")
            sys.exit(1)

        if qty < 1:
            print(f"Precondition FAILED: Position holds only {qty} shares (need at least 1).")
            print("No order placed.")
            return
        print("Precondition met: at least 1 share held.")

        # Submit sell order
        order_payload = {
            "symbol": "AAPL",
            "qty": "1",
            "side": "sell",
            "type": "market",
            "time_in_force": "day",
        }
        try:
            order_resp = requests.post(f"{base_url}/orders", headers=headers, json=order_payload)
            order_resp.raise_for_status()
            order_data = order_resp.json()
            print("Order placed successfully:")
            print(order_data)
        except Exception as e:
            print(f"Failed to place sell order: {e}")
            if order_resp is not None:
                print(f"Response: {order_resp.text}")
            sys.exit(1)

if __name__ == "__main__":
    main()