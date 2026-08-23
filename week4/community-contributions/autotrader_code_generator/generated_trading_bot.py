
import requests
import json
import time
import os
import collections
import argparse
import math
from dataclasses import dataclass
from typing import Dict, Any, Deque, Optional, List

# --- Assumptions ---
# 1. Historical Price Data Simulation: The simulated API's `/market/price` endpoint
#    only provides the current price. To implement SMA crossover, which requires
#    historical data, this bot simulates history by repeatedly calling `get_price`
#    over time and storing the results. It assumes that calling `get_price` at regular
#    intervals (e.g., every 5 seconds) effectively provides a time-series of prices.
# 2. API Response Formats:
#    - `get_price`: Assumed to return `{"symbol": "SYM", "price": 123.45}`.
#    - `get_balance`: Assumed to return `{"cash_balance": 10000.00, ...}`.
#    - `get_positions`: Assumed to return a list of dictionaries, e.
#      `[{"symbol": "SYM", "quantity": 10}, ...]`. If no position, an empty list or
#      a list without the symbol.
#    - `place_order`: Assumed to return `{"order_id": "...", "status": "accepted"}`.
# 3. Order Type: For `place_order`, `order_type` is assumed to be "MARKET" for simplicity,
#    as no other types are specified and "price_optional" implies it's for limit orders.
#    For MARKET orders, `price_optional` will not be sent.
# 4. Error Handling: Basic network and API-level error checking is implemented.
#    More complex retry logic or backoff strategies are not included to keep the example concise.
# 5. Time Zones: The API notes specify ISO timestamps in UTC. For internal logic,
#    `time.time()` (epoch seconds in UTC) is used for time comparisons, which is
#    sufficient for throttling and trade timing.

# --- Configuration ---
# You can override these defaults using command-line arguments.
DEFAULT_API_KEY = os.environ.get("SIM_API_KEY", "<YOUR_SIM_API_KEY>") # Set SIM_API_KEY env var or replace
DEFAULT_BASE_URL = "https://sim.example.com/api"
DEFAULT_SYMBOL = "AAPL" # Example stock symbol

# Trading Strategy Parameters
DEFAULT_SHORT_SMA_PERIOD = 5  # Number of price points for short SMA
DEFAULT_LONG_SMA_PERIOD = 20  # Number of price points for long SMA
DEFAULT_BUY_CASH_FRACTION = 0.95 # Fraction of available cash to use for a BUY order

# Bot Operation Parameters
DEFAULT_PRICE_FETCH_INTERVAL_SECONDS = 5 # How often to fetch a new price point for SMA calculation
DEFAULT_MAIN_LOOP_INTERVAL_SECONDS = 10 # How often the bot evaluates the strategy
DEFAULT_MIN_TIME_BETWEEN_TRADES_SECONDS = 60 # Minimum time (seconds) between placing orders
DEFAULT_INITIAL_HISTORY_COLLECTION_COUNT = DEFAULT_LONG_SMA_PERIOD + 5 # Ensure enough data for long SMA


@dataclass
class TradingBotConfig:
    api_key: str
    base_url: str
    symbol: str
    short_sma_period: int
    long_sma_period: int
    buy_cash_fraction: float
    price_fetch_interval_seconds: int
    main_loop_interval_seconds: int
    min_time_between_trades_seconds: int
    initial_history_collection_count: int
    dry_run: bool


class SimulatedAPIClient:
    """
    Client for interacting with the ExampleEquitySim API.
    Handles request building, authentication, and basic error parsing.
    """

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        self.session = requests.Session() # Use a session for connection pooling

    def _log(self, message: str) -> None:
        """Simple logging utility."""
        print(f"[API Client] {message}")

    def _make_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Generic helper to make API requests.
        """
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(
                method, url, headers=self.headers, params=params, json=json_data, timeout=10
            )
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.HTTPError as e:
            self._log(f"HTTP error for {method} {url}: {e.response.status_code} - {e.response.text}")
        except requests.exceptions.ConnectionError as e:
            self._log(f"Connection error for {method} {url}: {e}")
        except requests.exceptions.Timeout as e:
            self._log(f"Timeout error for {method} {url}: {e}")
        except requests.exceptions.RequestException as e:
            self._log(f"An unexpected request error occurred for {method} {url}: {e}")
        except json.JSONDecodeError:
            self._log(f"Failed to decode JSON from response for {method} {url}: {response.text}")
        return None

    def get_price(self, symbol: str) -> Optional[float]:
        """
        Fetches the current market price for a given symbol.
        Returns the price as a float, or None on error.
        """
        path = "/market/price"
        params = {"symbol": symbol}
        response = self._make_request("GET", path, params=params)
        if response and "price" in response:
            return float(response["price"])
        self._log(f"Could not get price for {symbol}.")
        return None

    def place_order(
        self,
        symbol: str,
        side: str, # "BUY" or "SELL"
        quantity: float,
        order_type: str = "MARKET",
        price_optional: Optional[float] = None # For LIMIT orders, not used for MARKET
    ) -> Optional[Dict[str, Any]]:
        """
        Places a trading order.
        """
        path = "/orders"
        payload = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "order_type": order_type,
        }
        if order_type != "MARKET" and price_optional is not None:
            payload["price_optional"] = price_optional

        self._log(f"Placing {side} order: {quantity} {symbol} ({order_type})...")
        response = self._make_request("POST", path, json_data=payload)
        if response and response.get("status") == "accepted":
            self._log(f"Order placed successfully: {response.get('order_id')}")
            return response
        self._log(f"Failed to place {side} order for {quantity} {symbol}. Response: {response}")
        return None

    def cancel_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Cancels an existing order.
        """
        path = f"/orders/{order_id}/cancel"
        self._log(f"Cancelling order {order_id}...")
        response = self._make_request("POST", path)
        if response and response.get("status") == "cancelled":
            self._log(f"Order {order_id} cancelled.")
            return response
        self._log(f"Failed to cancel order {order_id}. Response: {response}")
        return None

    def get_balance(self) -> Optional[float]:
        """
        Fetches the current cash balance.
        Returns cash balance as float, or None on error.
        """
        path = "/account/balance"
        response = self._make_request("GET", path)
        if response and "cash_balance" in response:
            return float(response["cash_balance"])
        self._log("Could not get account balance.")
        return None

    def get_positions(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetches all current open positions.
        Returns a list of position dictionaries, or None on error.
        """
        path = "/account/positions"
        response = self._make_request("GET", path)
        if response is not None:
            # Assuming the API returns a list, even if empty
            if isinstance(response, list):
                return response
            else:
                self._log(f"Unexpected response format for get_positions: {response}")
                return []
        self._log("Could not get account positions.")
        return None


class TradingBot:
    """
    Implements the SMA Crossover trading strategy for a simulated equities API.
    """

    def __init__(self, config: TradingBotConfig, api_client: SimulatedAPIClient):
        self.config = config
        self.api_client = api_client
        # Deque for efficient rolling window of prices
        self.price_history: Deque[float] = collections.deque(
            maxlen=self.config.long_sma_period
        )
        self.last_trade_timestamp: float = 0.0
        self.current_position_quantity: float = 0.0
        self.previous_short_sma: Optional[float] = None
        self.previous_long_sma: Optional[float] = None

        self._log(f"Trading bot initialized for symbol: {self.config.symbol}")
        self._log(f"Short SMA: {self.config.short_sma_period} periods, Long SMA: {self.config.long_sma_period} periods")
        if self.config.dry_run:
            self._log("!!! DRY RUN MODE ACTIVE - NO REAL ORDERS WILL BE PLACED !!!")

    def _log(self, message: str) -> None:
        """Simple logging utility for the bot."""
        print(f"[Bot] {message}")

    def _fetch_and_store_price(self) -> Optional[float]:
        """
        Fetches the current price from the API and adds it to the price history.
        Returns the fetched price or None if failed.
        """
        price = self.api_client.get_price(self.config.symbol)
        if price is not None:
            self.price_history.append(price)
            self._log(f"Fetched price for {self.config.symbol}: {price}. History size: {len(self.price_history)}")
            return price
        self._log(f"Failed to fetch current price for {self.config.symbol}.")
        return None

    def _calculate_sma(self, period: int) -> Optional[float]:
        """
        Calculates the Simple Moving Average (SMA) for a given period
        using the stored price history.
        """
        if len(self.price_history) < period:
            return None
        # Get the last 'period' prices from the deque
        # Python's deque doesn't have direct slicing like list[-period:]
        # So we convert to list for slicing or iterate last 'n' elements
        recent_prices = list(self.price_history)[-period:]
        return sum(recent_prices) / period

    def _update_current_position(self) -> None:
        """
        Fetches the current position for the trading symbol from the API
        and updates the bot's internal state.
        """
        positions = self.api_client.get_positions()
        self.current_position_quantity = 0.0
        if positions:
            for pos in positions:
                if pos.get("symbol") == self.config.symbol:
                    self.current_position_quantity = float(pos.get("quantity", 0))
                    break
        self._log(f"Current position in {self.config.symbol}: {self.current_position_quantity}")

    def _can_trade(self) -> bool:
        """
        Checks if enough time has passed since the last trade to place a new one.
        """
        time_since_last_trade = time.time() - self.last_trade_timestamp
        if time_since_last_trade < self.config.min_time_between_trades_seconds:
            self._log(f"Throttling: Waiting {math.ceil(self.config.min_time_between_trades_seconds - time_since_last_trade)}s before next trade.")
            return False
        return True

    def collect_initial_history(self) -> None:
        """
        Collects an initial set of price data before starting the trading strategy.
        This is crucial for calculating SMAs from the start.
        """
        self._log(f"Collecting initial price history ({self.config.initial_history_collection_count} points required)...")
        for i in range(self.config.initial_history_collection_count):
            if self._fetch_and_store_price() is None:
                self._log("Failed to collect initial price. Retrying...")
            # Wait before fetching next price to simulate time passing
            time.sleep(self.config.price_fetch_interval_seconds)
            self._log(f"Collected {i+1}/{self.config.initial_history_collection_count} prices.")
        self._log("Initial price history collection complete.")

    def run_strategy_iteration(self) -> None:
        """
        Executes one iteration of the SMA crossover strategy.
        """
        self._log("--- Running strategy iteration ---")

        # 1. Fetch current position and balance
        self._update_current_position()
        cash_balance = self.api_client.get_balance()
        if cash_balance is None:
            self._log("Could not get cash balance. Skipping iteration.")
            return

        # 2. Fetch new price and update history
        if self._fetch_and_store_price() is None:
            return # Skip iteration if price fetch fails

        # 3. Ensure enough data for SMAs
        if len(self.price_history) < self.config.long_sma_period:
            self._log(f"Not enough price history for SMAs (need {self.config.long_sma_period}, have {len(self.price_history)}). Waiting for more data.")
            return

        # 4. Calculate SMAs
        short_sma = self._calculate_sma(self.config.short_sma_period)
        long_sma = self._calculate_sma(self.config.long_sma_period)

        if short_sma is None or long_sma is None:
            self._log("Could not calculate SMAs. Skipping iteration.")
            return

        self._log(f"Current SMAs: Short={short_sma:.2f}, Long={long_sma:.2f}")

        # If this is the first time we calculated SMAs, just store them and exit
        if self.previous_short_sma is None or self.previous_long_sma is None:
            self._log("First SMA calculation. Storing values for next iteration comparison.")
            self.previous_short_sma = short_sma
            self.previous_long_sma = long_sma
            return

        # 5. Check for crossover signals
        # Buy Signal: Short SMA crosses above Long SMA
        if (self.previous_short_sma < self.previous_long_sma) and (short_sma >= long_sma):
            self._log("!!! BUY SIGNAL DETECTED: Short SMA crossed above Long SMA !!!")
            if self.current_position_quantity > 0:
                self._log(f"Already hold a position of {self.current_position_quantity} {self.config.symbol}. No new buy order.")
            elif not self._can_trade():
                pass # Message already logged by _can_trade()
            else:
                buy_amount_dollars = cash_balance * self.config.buy_cash_fraction
                # Use the most recent price for calculating quantity
                current_price = self.price_history[-1]
                if current_price > 0:
                    quantity_to_buy = math.floor(buy_amount_dollars / current_price)
                    if quantity_to_buy > 0:
                        self._log(f"Attempting to BUY {quantity_to_buy} shares of {self.config.symbol} at approx ${current_price:.2f} using ${buy_amount_dollars:.2f} of cash.")
                        if not self.config.dry_run:
                            order_response = self.api_client.place_order(self.config.symbol, "BUY", quantity_to_buy)
                            if order_response:
                                self.last_trade_timestamp = time.time()
                                self._update_current_position() # Refresh position after order
                        else:
                            self._log(f"DRY RUN: Would have placed BUY order for {quantity_to_buy} {self.config.symbol}.")
                            self.last_trade_timestamp = time.time() # Still simulate trade delay
                    else:
                        self._log("Calculated quantity to buy is zero.")
                else:
                    self._log("Current price is zero, cannot calculate buy quantity.")

        # Sell Signal: Short SMA crosses below Long SMA
        elif (self.previous_short_sma > self.previous_long_sma) and (short_sma <= long_sma):
            self._log("!!! SELL SIGNAL DETECTED: Short SMA crossed below Long SMA !!!")
            if self.current_position_quantity == 0:
                self._log("No open position to sell. No new sell order.")
            elif not self._can_trade():
                pass # Message already logged by _can_trade()
            else:
                quantity_to_sell = self.current_position_quantity
                self._log(f"Attempting to SELL {quantity_to_sell} shares of {self.config.symbol}.")
                if not self.config.dry_run:
                    order_response = self.api_client.place_order(self.config.symbol, "SELL", quantity_to_sell)
                    if order_response:
                        self.last_trade_timestamp = time.time()
                        self._update_current_position() # Refresh position after order
                else:
                    self._log(f"DRY RUN: Would have placed SELL order for {quantity_to_sell} {self.config.symbol}.")
                    self.last_trade_timestamp = time.time() # Still simulate trade delay

        else:
            self._log("No crossover signal detected.")

        # 6. Update previous SMA values for the next iteration
        self.previous_short_sma = short_sma
        self.previous_long_sma = long_sma

        self._log("--- Iteration complete ---")


def main():
    """
    Main function to parse arguments, configure the bot, and run the trading loop.
    """
    parser = argparse.ArgumentParser(
        description="SMA Crossover Trading Bot for Simulated Equities API."
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=DEFAULT_API_KEY,
        help=f"Your API key for the simulator. Default: '{DEFAULT_API_KEY}' (or SIM_API_KEY env var)"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=DEFAULT_BASE_URL,
        help=f"Base URL of the simulated API. Default: {DEFAULT_BASE_URL}"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default=DEFAULT_SYMBOL,
        help=f"Trading symbol (e.g., AAPL). Default: {DEFAULT_SYMBOL}"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="If set, the bot will log trade actions instead of placing real orders."
    )
    parser.add_argument(
        "--short-sma-period",
        type=int,
        default=DEFAULT_SHORT_SMA_PERIOD,
        help=f"Number of periods for the short SMA. Default: {DEFAULT_SHORT_SMA_PERIOD}"
    )
    parser.add_argument(
        "--long-sma-period",
        type=int,
        default=DEFAULT_LONG_SMA_PERIOD,
        help=f"Number of periods for the long SMA. Default: {DEFAULT_LONG_SMA_PERIOD}"
    )
    parser.add_argument(
        "--buy-cash-fraction",
        type=float,
        default=DEFAULT_BUY_CASH_FRACTION,
        help=f"Fraction of available cash to use for a BUY order (e.g., 0.95). Default: {DEFAULT_BUY_CASH_FRACTION}"
    )
    parser.add_argument(
        "--price-fetch-interval",
        type=int,
        default=DEFAULT_PRICE_FETCH_INTERVAL_SECONDS,
        help=f"Interval in seconds to fetch new price data for SMA calculation. Default: {DEFAULT_PRICE_FETCH_INTERVAL_SECONDS}"
    )
    parser.add_argument(
        "--main-loop-interval",
        type=int,
        default=DEFAULT_MAIN_LOOP_INTERVAL_SECONDS,
        help=f"Interval in seconds between strategy evaluations. Default: {DEFAULT_MAIN_LOOP_INTERVAL_SECONDS}"
    )
    parser.add_argument(
        "--min-trade-interval",
        type=int,
        default=DEFAULT_MIN_TIME_BETWEEN_TRADES_SECONDS,
        help=f"Minimum time in seconds between placing actual orders. Default: {DEFAULT_MIN_TIME_BETWEEN_TRADES_SECONDS}"
    )
    parser.add_argument(
        "--initial-history-count",
        type=int,
        default=DEFAULT_INITIAL_HISTORY_COLLECTION_COUNT,
        help=f"Number of initial price points to collect before starting strategy. Default: {DEFAULT_INITIAL_HISTORY_COLLECTION_COUNT}"
    )
    parser.add_argument(
        "--run-duration",
        type=int,
        default=300, # Default to 5 minutes for demonstration
        help="Total duration in seconds to run the bot loop. (0 for indefinite run)."
    )

    args = parser.parse_args()

    if args.api_key == "<YOUR_SIM_API_KEY>":
        print("WARNING: API Key is not set. Please replace <YOUR_SIM_API_KEY> in the script or set SIM_API_KEY environment variable, or pass with --api-key.")
        print("Exiting...")
        return

    config = TradingBotConfig(
        api_key=args.api_key,
        base_url=args.base_url,
        symbol=args.symbol,
        short_sma_period=args.short_sma_period,
        long_sma_period=args.long_sma_period,
        buy_cash_fraction=args.buy_cash_fraction,
        price_fetch_interval_seconds=args.price_fetch_interval,
        main_loop_interval_seconds=args.main_loop_interval,
        min_time_between_trades_seconds=args.min_trade_interval,
        initial_history_collection_count=args.initial_history_count,
        dry_run=args.dry_run,
    )

    api_client = SimulatedAPIClient(config.base_url, config.api_key)
    trading_bot = TradingBot(config, api_client)

    # Ensure enough history for SMA calculations
    if config.initial_history_collection_count < config.long_sma_period:
        trading_bot._log(f"WARNING: Initial history collection count ({config.initial_history_collection_count}) is less than long SMA period ({config.long_sma_period}). Adjusting to {config.long_sma_period + 5}.")
        config.initial_history_collection_count = config.long_sma_period + 5

    # Collect initial price data
    trading_bot.collect_initial_history()

    # Main trading loop
    start_time = time.time()
    iteration = 0
    trading_bot._log(f"Starting main trading loop for {args.run_duration} seconds (0 for indefinite)...")

    try:
        while True:
            iteration += 1
            trading_bot._log(f"\n--- Main Loop Iteration {iteration} ---")
            trading_bot.run_strategy_iteration()

            if args.run_duration > 0 and (time.time() - start_time) >= args.run_duration:
                trading_bot._log(f"Run duration of {args.run_duration} seconds completed. Exiting.")
                break

            trading_bot._log(f"Sleeping for {config.main_loop_interval_seconds} seconds...")
            time.sleep(config.main_loop_interval_seconds)

    except KeyboardInterrupt:
        trading_bot._log("Bot stopped manually by user (KeyboardInterrupt).")
    except Exception as e:
        trading_bot._log(f"An unexpected error occurred in the main loop: {e}")
    finally:
        trading_bot._log("Trading bot shutting down.")


if __name__ == "__main__":
    # --- Demonstration Run ---
    # To run this example:
    # 1. Save this script as `generated_trading_bot.py`.
    # 2. Install requests: `pip install requests`
    # 3. Replace `<YOUR_SIM_API_KEY>` with an actual API key or set the SIM_API_KEY environment variable.
    # 4. Run from your terminal:
    #    `python generated_trading_bot.py --dry-run --run-duration 60 --symbol MSFT`
    # This will simulate a 60-second run for MSFT in dry-run mode,
    # printing potential trades without actually executing them.
    # For a longer run, change --run-duration (e.g., 3600 for 1 hour).
    # Remove --dry-run to enable live trading (use with caution!).
    main()
