"""
Simulated equities API for testing LLM-generated trading bots.
Uses only stdlib (no Flask). Serves the API spec endpoints in-memory.
Run: python simulator.py [--port 8765] [--api-key sim-key-123]
"""

import json
import random
import argparse
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from threading import Thread

# In-memory state (shared across requests)
INITIAL_CASH = 10_000.0
DEFAULT_SYMBOLS = {"AAPL": 150.0, "MSFT": 380.0, "GOOGL": 140.0}
# Price random walk: last price per symbol, updated on each get_price
_state = {
    "cash": INITIAL_CASH,
    "positions": {},  # symbol -> quantity (int)
    "order_counter": 0,
    "orders": {},  # order_id -> {symbol, side, quantity, status}
    "prices": dict(DEFAULT_SYMBOLS),  # symbol -> float, evolves with random walk
}
# Auth: accept any key by default; set SIM_REQUIRED_API_KEY to enforce
REQUIRED_API_KEY = None  # set via --api-key or env
_api_key = None


def _price_for(symbol: str) -> float:
    """Current price with small random walk."""
    if symbol not in _state["prices"]:
        _state["prices"][symbol] = 100.0 + random.uniform(-20, 20)
    p = _state["prices"][symbol]
    change = random.gauss(0, 1.5)
    _state["prices"][symbol] = max(1.0, p + change)
    return round(_state["prices"][symbol], 2)


def _check_auth(handler: BaseHTTPRequestHandler) -> bool:
    if _api_key is None:
        return True
    key = handler.headers.get("X-API-KEY") or handler.headers.get("x-api-key")
    return key == _api_key


def _send_json(handler: BaseHTTPRequestHandler, status: int, data: dict) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode("utf-8"))


def _send_error(handler: BaseHTTPRequestHandler, status: int, message: str) -> None:
    _send_json(handler, status, {"error": message})


class SimulatorHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # quiet by default

    def do_GET(self):
        if not _check_auth(self):
            _send_error(self, 401, "Invalid or missing X-API-KEY")
            return
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        # GET /api/market/price or /market/price?symbol=AAPL
        if path in ("/api/market/price", "/market/price") or path.endswith("/market/price"):
            symbol = (qs.get("symbol") or [""])[0].upper() or "AAPL"
            price = _price_for(symbol)
            _send_json(self, 200, {"symbol": symbol, "price": price})
            return

        # GET /api/account/balance or /account/balance
        if path in ("/api/account/balance", "/account/balance") or path.endswith("/account/balance"):
            _send_json(
                self,
                200,
                {
                    "cash_balance": round(_state["cash"], 2),
                    "currency": "USD",
                    "as_of": datetime.now(timezone.utc).isoformat(),
                },
            )
            return

        # GET /api/account/positions or /account/positions
        if path in ("/api/account/positions", "/account/positions") or path.endswith("/account/positions"):
            positions = [
                {"symbol": s, "quantity": q}
                for s, q in _state["positions"].items()
                if q != 0
            ]
            _send_json(self, 200, positions)
            return

        _send_error(self, 404, f"Unknown path: {path}")

    def do_POST(self):
        if not _check_auth(self):
            _send_error(self, 401, "Invalid or missing X-API-KEY")
            return
        parsed = urlparse(self.path)
        path = parsed.path

        # POST /api/orders or /orders
        if path in ("/api/orders", "/orders") or (path.endswith("/orders") and "/cancel" not in path):
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                _send_error(self, 400, "JSON body required")
                return
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except json.JSONDecodeError:
                _send_error(self, 400, "Invalid JSON")
                return
            symbol = (body.get("symbol") or "AAPL").upper()
            side = (body.get("side") or "buy").lower()
            quantity = int(body.get("quantity") or 0)
            if quantity <= 0:
                _send_error(self, 400, "quantity must be positive")
                return
            price = _price_for(symbol)
            _state["order_counter"] += 1
            order_id = f"ord-{_state['order_counter']}"
            if side == "buy":
                cost = price * quantity
                if cost > _state["cash"]:
                    _send_json(
                        self,
                        400,
                        {"error": "Insufficient cash", "order_id": None},
                    )
                    return
                _state["cash"] -= cost
                _state["positions"][symbol] = _state["positions"].get(symbol, 0) + quantity
            else:
                have = _state["positions"].get(symbol, 0)
                if quantity > have:
                    _send_error(self, 400, "Insufficient position to sell")
                    return
                _state["cash"] += price * quantity
                _state["positions"][symbol] = have - quantity
                if _state["positions"][symbol] == 0:
                    del _state["positions"][symbol]
            _state["orders"][order_id] = {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "status": "filled",
            }
            _send_json(
                self,
                200,
                {"order_id": order_id, "status": "accepted", "filled": True},
            )
            return

        # POST /api/orders/{order_id}/cancel
        if "/orders/" in path and "/cancel" in path:
            parts = path.split("/")
            try:
                idx = parts.index("orders")
                order_id = parts[idx + 1] if idx + 1 < len(parts) else None
            except (ValueError, IndexError):
                order_id = None
            if not order_id or order_id == "cancel":
                _send_error(self, 404, "order_id not found in path")
                return
            if order_id in _state["orders"]:
                _state["orders"][order_id]["status"] = "cancelled"
                _send_json(self, 200, {"order_id": order_id, "status": "cancelled"})
            else:
                _send_json(self, 404, {"error": "Order not found"})
            return

        _send_error(self, 404, f"Unknown path: {path}")


def run_server(port: int = 8765, api_key: str | None = None):
    global _api_key
    _api_key = api_key
    server = HTTPServer(("127.0.0.1", port), SimulatorHandler)
    server.serve_forever()


def start_simulator_background(port: int = 8765, api_key: str = "sim-key-123"):
    """Start the simulator in a background thread. Returns the thread and base URL."""
    thread = Thread(target=run_server, kwargs={"port": port, "api_key": api_key}, daemon=True)
    thread.start()
    import time
    time.sleep(0.3)  # allow server to bind
    return thread, f"http://127.0.0.1:{port}/api"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run simulated equities API")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind")
    parser.add_argument("--api-key", type=str, default="sim-key-123", help="API key to require (X-API-KEY)")
    args = parser.parse_args()
    run_server(port=args.port, api_key=args.api_key)
