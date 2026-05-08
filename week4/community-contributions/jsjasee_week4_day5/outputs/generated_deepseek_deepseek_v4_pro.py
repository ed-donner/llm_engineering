import os
import sys
import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv not installed, but environment variables may still be present

# Read credentials
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_PAPER_ENDPOINT = os.getenv(
    "ALPACA_PAPER_ENDPOINT", "https://paper-api.alpaca.markets/v2"
)

# Validate essential credentials
if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    print(
        "Error: Missing Alpaca API credentials. Ensure ALPACA_API_KEY and ALPACA_SECRET_KEY are set in .env or environment."
    )
    sys.exit(1)

# Set up base URLs
TRADING_API_BASE = ALPACA_PAPER_ENDPOINT.rstrip("/")
DATA_API_BASE = "https://data.alpaca.markets/v2"  # Real market data endpoint

HEADERS = {
    "APCA-API-KEY-ID": ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
}

SYMBOL = "AAPL"
TARGET_BUY_PRICE = 180
TARGET_SELL_PRICE = 190
SHARES = 1


def get_latest_trade_price(symbol):
    """Fetch the latest trade price for a symbol using Alpaca Data API v2."""
    url = f"{DATA_API_BASE}/stocks/{symbol}/trades/latest"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        trade = data.get("trade")
        if trade and "p" in trade:
            return float(trade["p"])
        else:
            print(f"Error: Unexpected response structure: {data}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching latest trade for {symbol}: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response body: {e.response.text}")
        return None


def get_account():
    """Fetch account information from Alpaca."""
    url = f"{TRADING_API_BASE}/account"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching account: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response body: {e.response.text}")
        return None


def get_position(symbol):
    """Fetch current position for a symbol. Returns quantity (int) or 0 if no position."""
    url = f"{TRADING_API_BASE}/positions/{symbol}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            pos = resp.json()
            return int(pos.get("qty", 0))
        elif resp.status_code == 404:
            return 0  # No position exists
        else:
            resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching position for {symbol}: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response body: {e.response.text}")
        return None  # Error case


def place_order(symbol, qty, side):
    """Submit a market order to buy or sell."""
    url = f"{TRADING_API_BASE}/orders"
    payload = {
        "symbol": symbol,
        "qty": str(qty),
        "side": side,
        "type": "market",
        "time_in_force": "day",
    }
    try:
        resp = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error placing {side} order for {qty} shares of {symbol}: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response body: {e.response.text}")
        return None


def main():
    print(f"Fetching latest trade price for {SYMBOL}...")
    price = get_latest_trade_price(SYMBOL)
    if price is None:
        print("Unable to fetch latest trade price. Exiting.")
        sys.exit(1)

    print(f"Latest {SYMBOL} trade price: ${price:.2f}")

    # Decision logic
    if price < TARGET_BUY_PRICE:
        print(
            f"Price ${price:.2f} is below ${TARGET_BUY_PRICE}. Checking buying power for buy order."
        )
        account = get_account()
        if account is None:
            print("Failed to retrieve account information. Exiting.")
            sys.exit(1)

        buying_power = float(account.get("buying_power", 0))
        print(f"Current buying power: ${buying_power:.2f}")

        if buying_power >= price:
            print(
                f"Placing BUY order for {SHARES} share(s) of {SYMBOL} at market price."
            )
            order_response = place_order(SYMBOL, SHARES, "buy")
            if order_response:
                print(f"Order submitted successfully: {order_response}")
            else:
                print("Order submission failed.")
        else:
            print(
                f"Insufficient buying power to buy 1 share. Required: ~${price:.2f}, Available: ${buying_power:.2f}. Skipping order."
            )

    elif price > TARGET_SELL_PRICE:
        print(
            f"Price ${price:.2f} is above ${TARGET_SELL_PRICE}. Checking position for sell order."
        )
        qty = get_position(SYMBOL)
        if qty is None:
            print("Failed to retrieve position information. Exiting.")
            sys.exit(1)

        print(f"Current {SYMBOL} position: {qty} share(s)")
        if qty >= SHARES:
            print(
                f"Placing SELL order for {SHARES} share(s) of {SYMBOL} at market price."
            )
            order_response = place_order(SYMBOL, SHARES, "sell")
            if order_response:
                print(f"Order submitted successfully: {order_response}")
            else:
                print("Order submission failed.")
        else:
            print(
                f"Insufficient shares to sell. Required: {SHARES}, Held: {qty}. Skipping order."
            )

    else:  # 180 <= price <= 190
        print(
            f"Price ${price:.2f} is within the neutral range (${TARGET_BUY_PRICE} - ${TARGET_SELL_PRICE}). No action taken."
        )


if __name__ == "__main__":
    main()
