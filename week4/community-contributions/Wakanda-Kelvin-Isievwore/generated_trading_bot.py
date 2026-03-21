import requests
import time
import argparse
from collections import deque

API_KEY = '<SIM_API_KEY>'
BASE_URL = "https://sim.example.com/api"

HEADERS = {
    "X-API-KEY": API_KEY
}

SYMBOL = "AAPL"
SHORT_WINDOW = 5
LONG_WINDOW = 20
MIN_TIME_BETWEEN_TRADES_SECONDS = 60
CASH_ALLOCATION_FOR_TRADES = 0.1

def get_price(symbol):
    try:
        response = requests.get(f"{BASE_URL}/market/price", headers=HEADERS, params={"symbol": symbol})
        response.raise_for_status()
        return response.json().get('price')
    except requests.RequestException as e:
        print(f"Error getting price for {symbol}: {e}")
        return None

def place_order(symbol, side, quantity, order_type="market", price_optional=None):
    order_details = {
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "order_type": order_type
    }
    if price_optional:
        order_details["price_optional"] = price_optional
    try:
        response = requests.post(f"{BASE_URL}/orders", headers=HEADERS, json=order_details)
        response.raise_for_status()
        print(f"Order {side} {quantity} of {symbol} placed.")
        return response.json()
    except requests.RequestException as e:
        print(f"Error placing order for {symbol}: {e}")
        return None

def get_balance():
    try:
        response = requests.get(f"{BASE_URL}/account/balance", headers=HEADERS)
        response.raise_for_status()
        return response.json().get('cash')
    except requests.RequestException as e:
        print(f"Error getting balance: {e}")
        return None

def sma_moving_average(prices, window):
    if len(prices) < window:
        return None
    return sum(prices[-window:]) / window

def sma_crossover(dry_run):
    prices = deque(maxlen=LONG_WINDOW)
    last_action_time = 0
    last_sma_short, last_sma_long = None, None

    while True:
        price = get_price(SYMBOL)
        if price is not None:
            prices.append(price)

        if len(prices) >= LONG_WINDOW:
            sma_short = sma_moving_average(prices, SHORT_WINDOW)
            sma_long = sma_moving_average(prices, LONG_WINDOW)

            if sma_short is not None and sma_long is not None:
                now = time.time()
                if now - last_action_time >= MIN_TIME_BETWEEN_TRADES_SECONDS:
                    if sma_short > sma_long and (last_sma_short is None or last_sma_short <= last_sma_long):
                        cash = get_balance()
                        if cash:
                            quantity = (cash * CASH_ALLOCATION_FOR_TRADES) / price
                            if dry_run:
                                print(f"Dry-run: BUY {quantity:.2f} of {SYMBOL} at price {price}")
                            else:
                                place_order(SYMBOL, "buy", quantity)
                            last_action_time = now
                    elif sma_short < sma_long and (last_sma_short is None or last_sma_short >= last_sma_long):
                        # Simplified sell logic, assume full sell of one unit for demo
                        if dry_run:
                            print(f"Dry-run: SELL 1.00 of {SYMBOL} at price {price}")
                        else:
                            place_order(SYMBOL, "sell", 1)  # Example logic to sell 1 unit
                        last_action_time = now

                last_sma_short, last_sma_long = sma_short, sma_long

        time.sleep(5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the SMA crossover trading bot.")
    parser.add_argument("--dry-run", action='store_true', help="Run the bot without placing trades.")
    args = parser.parse_args()

    # Run demo:
    end_time = time.time() + 60  # Run for 60 seconds
    while time.time() < end_time:
        sma_crossover(args.dry_run)
        time.sleep(1)