"""Alpaca adapter for the notebook: daily data, order preview, and paper submission."""

import hashlib
import math
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
from alpaca.common.exceptions import APIError
from alpaca.data.enums import Adjustment, DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import (
    GetCalendarRequest,
    GetOrdersRequest,
    LimitOrderRequest,
)

from strategy_lab import validate_bars


NY = ZoneInfo("America/New_York")


class PaperBroker:
    """Paper-only, one symbol, whole shares, no shorting or borrowing.

    Use a dedicated paper account: this adapter treats ALL holdings of the chosen
    symbol as its position. It is a one-shot demo, not an unattended trading loop.
    """

    def __init__(self):
        key = os.environ.get("ALPACA_PAPER_API_KEY")
        secret = os.environ.get("ALPACA_PAPER_SECRET_KEY")
        if not key or not secret:
            raise ValueError(
                "Set ALPACA_PAPER_API_KEY and ALPACA_PAPER_SECRET_KEY in .env."
            )
        self.trading = TradingClient(key, secret, paper=True)
        self.data = StockHistoricalDataClient(key, secret)

    def connection_status(self):
        """Verify credentials without placing orders, including outside market hours."""
        account = self.trading.get_account()
        clock = self.trading.get_clock()
        return {
            "environment": "paper",
            "account_status": str(account.status),
            "cash": str(account.cash),
            "equity": str(account.equity),
            "trading_blocked": bool(
                account.trading_blocked
                or account.account_blocked
                or account.trade_suspended_by_user
            ),
            "market_open": bool(clock.is_open),
            "next_open": str(clock.next_open),
        }

    def bars(self, symbol, start, end):
        """IEX daily bars with split adjustment; end is exclusive."""
        start, end = pd.Timestamp(start), pd.Timestamp(end)
        start = start.tz_localize(NY) if start.tzinfo is None else start
        end = end.tz_localize(NY) if end.tzinfo is None else end
        if end > pd.Timestamp.now(tz=NY).normalize():
            raise ValueError("End must exclude today's incomplete daily bar.")
        response = self.data.get_stock_bars(
            StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start.to_pydatetime(),
                end=end.to_pydatetime(),
                adjustment=Adjustment.SPLIT,
                feed=DataFeed.IEX,
            )
        )
        if not response.data.get(symbol):
            raise ValueError(
                "No bars returned; check symbol, dates, and data entitlement."
            )
        frame = response.df.xs(symbol).sort_index()[["open", "close"]]
        frame = frame.loc[(frame.index >= start) & (frame.index < end)]
        validate_bars(frame)
        return frame

    def _existing_order(self, client_id):
        try:
            return self.trading.get_order_by_client_id(client_id)
        except APIError as exc:
            if exc.status_code == 404:
                return None
            raise  # Authentication/network failures must not mean "no order".

    def preview(self, strategy, symbol="AAPL", max_notional=1000.0, allocation=0.1):
        """Read-only preflight; calculate a limit order from current account state."""
        if (
            not math.isfinite(max_notional)
            or not 0 < max_notional <= 1000
            or not math.isfinite(allocation)
            or not 0 < allocation <= 0.1
        ):
            raise ValueError("Demo caps: $1,000 per entry and 10% of account equity.")
        symbol = symbol.strip().upper()
        now = datetime.now(NY)
        clock = self.trading.get_clock()
        if not clock.is_open:
            return {"action": "hold", "reason": "Regular market session is closed."}
        account = self.trading.get_account()
        if (
            account.trading_blocked
            or account.account_blocked
            or account.trade_suspended_by_user
        ):
            raise ValueError("Paper account does not currently permit trading.")
        asset = self.trading.get_asset(symbol)
        if not asset.tradable or str(asset.asset_class) not in (
            "us_equity",
            "AssetClass.US_EQUITY",
        ):
            raise ValueError("Choose a tradable US equity.")
        orders = self.trading.get_orders(
            filter=GetOrdersRequest(
                status=QueryOrderStatus.OPEN,
                symbols=[symbol],
                limit=1,
            )
        )
        if orders:
            return {
                "action": "hold",
                "reason": "An order for this symbol is already open.",
            }
        today = now.date()
        sessions = self.trading.get_calendar(
            filters=GetCalendarRequest(
                start=today - timedelta(days=14),
                end=today - timedelta(days=1),
            )
        )
        if not sessions:
            raise ValueError("Could not determine the preceding trading session.")
        expected_date = max(s.date for s in sessions)
        bars = self.bars(symbol, today - timedelta(days=180), today)
        last_date = bars.index[-1].tz_convert(NY).date()
        if last_date != expected_date or len(bars) < 30:
            raise ValueError(
                "Missing the latest completed session or insufficient warmup."
            )
        desired = strategy(bars.close.tolist())
        if type(desired) is not int or desired not in (0, 1):
            raise ValueError("Expected integer signal 0 or 1.")
        positions = self.trading.get_all_positions()
        position = next((p for p in positions if p.symbol == symbol), None)
        qty_owned = float(position.qty) if position else 0.0
        if not math.isfinite(qty_owned) or qty_owned < 0 or not qty_owned.is_integer():
            raise ValueError("This demo requires a flat or whole-share long position.")
        if (desired == 1 and qty_owned > 0) or (desired == 0 and qty_owned == 0):
            return {
                "action": "hold",
                "reason": "Current position already matches the signal.",
                "signal": desired,
                "signal_date": str(last_date),
            }
        side = "buy" if desired else "sell"
        quote = self.data.get_stock_latest_quote(
            StockLatestQuoteRequest(
                symbol_or_symbols=symbol,
                feed=DataFeed.IEX,
            )
        )[symbol]
        age = (now - quote.timestamp).total_seconds()
        bid, ask = float(quote.bid_price), float(quote.ask_price)
        if (
            not -5 <= age <= 120
            or not all(math.isfinite(x) for x in (bid, ask))
            or not 1 <= bid <= ask
        ):
            raise ValueError(
                "Need an IEX quote under 2 minutes old with valid prices >= $1."
            )
        limit = round(ask * 1.001 if side == "buy" else bid * 0.999, 2)
        budget = min(
            max_notional,
            float(account.equity) * allocation,
            max(0, float(account.cash)) * 0.98,
        )
        qty = math.floor(budget / limit) if side == "buy" else int(qty_owned)
        if qty <= 0:
            return {"action": "hold", "reason": "Budget cannot cover one whole share."}
        # Stable across cell reruns; a new code version or completed session changes it.
        fingerprint = f"{strategy.digest}:{symbol}:{last_date}:{side}"
        client_id = "w4-" + hashlib.sha256(fingerprint.encode()).hexdigest()[:32]
        existing = self._existing_order(client_id)
        if existing is not None:
            return {
                "action": "hold",
                "reason": "This strategy/session order already exists.",
                "client_order_id": client_id,
                "status": str(existing.status),
            }
        return {
            "action": side,
            "symbol": symbol,
            "qty": qty,
            "limit_price": limit,
            "estimated_notional": round(qty * limit, 2),
            "signal_date": str(last_date),
            "client_order_id": client_id,
            "environment": "paper",
        }

    def submit(
        self,
        strategy,
        reviewed_plan,
        symbol="AAPL",
        max_notional=1000.0,
        allocation=0.1,
    ):
        """Revalidate immediately; a changed plan must be previewed again."""
        current = self.preview(strategy, symbol, max_notional, allocation)
        if current != reviewed_plan or current.get("action") not in ("buy", "sell"):
            raise ValueError(
                "Order plan changed or is HOLD. Preview again before submitting."
            )
        request = LimitOrderRequest(
            symbol=current["symbol"],
            qty=current["qty"],
            side=OrderSide.BUY if current["action"] == "buy" else OrderSide.SELL,
            limit_price=current["limit_price"],
            time_in_force=TimeInForce.DAY,
            client_order_id=current["client_order_id"],
        )
        try:
            order = self.trading.submit_order(order_data=request)
        except Exception:
            # A timeout may occur AFTER acceptance. Reconcile; never blindly resubmit.
            order = self._existing_order(current["client_order_id"])
            if order is None:
                raise
        return {
            "client_order_id": order.client_order_id,
            "status": str(order.status),
            "filled_qty": str(order.filled_qty),
            "filled_avg_price": order.filled_avg_price,
        }

    def order_status(self, client_id):
        order = self.trading.get_order_by_client_id(client_id)
        return {
            "status": str(order.status),
            "filled_qty": str(order.filled_qty),
            "filled_avg_price": order.filled_avg_price,
        }
