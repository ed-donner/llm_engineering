"""Small Python strategy language, LLM generation, and chronological backtesting."""

import ast
import hashlib
import math
import operator
import time

import numpy as np
import pandas as pd


API_CONTRACT = """Write exactly one Python function: def signal(closes):
closes is a list of positive daily closing prices, oldest first, through today.
Return integer 1 to hold a long position, or integer 0 to hold cash.
Use only: local assignments, if/else, return, numeric constants, comparisons,
and/or/not, + - * /, indexing/slicing closes, and len/sum/min/max/abs.
No imports, loops, attributes, comprehensions, annotations, default arguments,
other functions, I/O, orders, or external state. Handle insufficient history.
The host decides position size and executes orders; you only choose 0 or 1.
Return Python source only, without Markdown fences.
"""

DEFAULT_SPEC = """Return 0 with fewer than 30 closes. Otherwise return 1 exactly
when the arithmetic mean of the last 10 closes is strictly greater than the
arithmetic mean of the last 30 closes. Return 0 otherwise, including ties."""

REFERENCE_SOURCE = """def signal(closes):
    if len(closes) < 30:
        return 0
    fast = sum(closes[-10:]) / 10
    slow = sum(closes[-30:]) / 30
    if fast > slow:
        return 1
    return 0
"""


class StrategyError(ValueError):
    """Source or behavior violates the documented strategy contract."""


class Strategy:
    """Interpret a deliberately small Python subset; never exec generated text.

    This is an educational interpreter, not a general Python sandbox. Unsupported
    syntax is rejected even when it would be valid in ordinary Python.
    """

    calls = {"len": len, "sum": sum, "min": min, "max": max, "abs": abs}
    binary = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }
    compare = {
        ast.Gt: operator.gt,
        ast.Lt: operator.lt,
        ast.GtE: operator.ge,
        ast.LtE: operator.le,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
    }
    allowed = (
        ast.Module,
        ast.FunctionDef,
        ast.arguments,
        ast.arg,
        ast.Assign,
        ast.If,
        ast.Return,
        ast.Name,
        ast.Load,
        ast.Store,
        ast.Constant,
        ast.BinOp,
        ast.UnaryOp,
        ast.USub,
        ast.UAdd,
        ast.Not,
        ast.Compare,
        ast.BoolOp,
        ast.And,
        ast.Or,
        ast.Call,
        ast.Subscript,
        ast.Slice,
        *binary,
        *compare,
    )

    def __init__(self, source):
        if not isinstance(source, str) or len(source) > 6000:
            raise StrategyError("Source must be text of at most 6000 characters.")
        try:
            tree = ast.parse(source)
        except (SyntaxError, RecursionError) as exc:
            raise StrategyError("Invalid Python source.") from exc
        nodes = list(ast.walk(tree))
        if len(nodes) > 400 or any(not isinstance(n, self.allowed) for n in nodes):
            raise StrategyError("Unsupported syntax or more than 400 AST nodes.")
        if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
            raise StrategyError("Define only signal(closes).")
        fn = tree.body[0]
        args = fn.args
        if (
            fn.name != "signal"
            or fn.decorator_list
            or fn.returns
            or len(args.args) != 1
            or args.args[0].arg != "closes"
            or args.args[0].annotation
            or args.defaults
            or args.kwonlyargs
            or args.posonlyargs
            or args.vararg
            or args.kwarg
            or getattr(fn, "type_params", [])
        ):
            raise StrategyError("Expected def signal(closes) without annotations.")
        for n in nodes:
            if isinstance(n, ast.FunctionDef) and n is not fn:
                raise StrategyError("Nested functions are unsupported.")
            if isinstance(n, ast.Constant):
                if (
                    type(n.value) not in (int, float)
                    or not math.isfinite(n.value)
                    or abs(n.value) > 1e6
                ):
                    raise StrategyError("Only finite numeric literals up to 1e6.")
            if isinstance(n, ast.Name) and n.id.startswith("_"):
                raise StrategyError("Private names are unsupported.")
            if isinstance(n, ast.Assign):
                if (
                    len(n.targets) != 1
                    or not isinstance(n.targets[0], ast.Name)
                    or n.targets[0].id in {"closes", *self.calls}
                ):
                    raise StrategyError("Assign to a new local name only.")
            if isinstance(n, ast.Call):
                if (
                    not isinstance(n.func, ast.Name)
                    or n.func.id not in self.calls
                    or n.keywords
                    or len(n.args) != 1
                ):
                    raise StrategyError("Use len/sum/min/max/abs with one argument.")
        self.source, self.body = source, fn.body
        self.digest = hashlib.sha256(source.encode()).hexdigest()[:16]

    def __call__(self, closes):
        if len(closes) > 10000:
            raise StrategyError("History exceeds 10,000 bars.")
        values = [float(v) for v in closes]
        if any(not math.isfinite(v) or v <= 0 for v in values):
            raise StrategyError("Closes must be finite and positive.")
        env = {"closes": values}

        def number(value):
            if type(value) not in (int, float, bool) or not math.isfinite(value):
                raise StrategyError("Expected finite numeric value.")
            if abs(value) > 1e15:
                raise StrategyError("Intermediate value exceeds 1e15.")
            return value

        def evaluate(n):
            if isinstance(n, ast.Constant):
                return n.value
            if isinstance(n, ast.Name):
                return env[n.id]
            if isinstance(n, ast.BinOp):
                return number(
                    self.binary[type(n.op)](
                        number(evaluate(n.left)), number(evaluate(n.right))
                    )
                )
            if isinstance(n, ast.UnaryOp):
                value = number(evaluate(n.operand))
                return (
                    not value
                    if isinstance(n.op, ast.Not)
                    else (-value if isinstance(n.op, ast.USub) else value)
                )
            if isinstance(n, ast.BoolOp):
                for item in n.values:
                    value = number(evaluate(item))
                    if isinstance(n.op, ast.And) and not value:
                        return value
                    if isinstance(n.op, ast.Or) and value:
                        return value
                return value
            if isinstance(n, ast.Compare):
                left = number(evaluate(n.left))
                for op, right_node in zip(n.ops, n.comparators):
                    right = number(evaluate(right_node))
                    if not self.compare[type(op)](left, right):
                        return False
                    left = right
                return True
            if isinstance(n, ast.Call):
                return number(self.calls[n.func.id](evaluate(n.args[0])))
            if isinstance(n, ast.Subscript):
                value = evaluate(n.value)
                if not isinstance(value, list):
                    raise StrategyError("Only price lists can be indexed.")
                if isinstance(n.slice, ast.Slice):
                    parts = [
                        evaluate(x) if x is not None else None
                        for x in (n.slice.lower, n.slice.upper, n.slice.step)
                    ]
                    return value[slice(*parts)]
                return value[evaluate(n.slice)]
            raise StrategyError("Unsupported expression.")

        def block(statements):
            for n in statements:
                if isinstance(n, ast.Return):
                    return True, evaluate(n.value)
                if isinstance(n, ast.Assign):
                    env[n.targets[0].id] = evaluate(n.value)
                elif isinstance(n, ast.If):
                    returned, value = block(n.body if evaluate(n.test) else n.orelse)
                    if returned:
                        return True, value
            return False, None

        try:
            returned, result = block(self.body)
            if not returned or type(result) is not int or result not in (0, 1):
                raise StrategyError("Every path must return integer 0 or 1.")
            return result
        except (
            KeyError,
            TypeError,
            ValueError,
            ArithmeticError,
            IndexError,
            RecursionError,
        ) as exc:
            raise StrategyError(str(exc)) from exc


def acceptance_cases():
    """Behavioral examples for DEFAULT_SPEC, not universal trading tests."""
    return [
        ([], 0),
        ([100.0] * 29, 0),
        ([100.0] * 30, 0),
        (list(range(1, 41)), 1),
        (list(range(40, 0, -1)), 0),
        ([200.0] * 20 + [100.0] * 10, 0),
    ]


def check_cases(strategy, cases):
    for closes, expected in cases:
        actual = strategy(closes)
        if actual != expected:
            raise StrategyError(
                f"For closes={closes}, expected {expected}, got {actual}."
            )


def generate_strategy(client, model, specification, cases, max_attempts=2):
    """Bounded generate/validate/repair loop; no broker data enters the prompt."""
    if not 1 <= max_attempts <= 3:
        raise ValueError("Choose one to three attempts.")
    prompt, records = specification, []
    for attempt in range(1, max_attempts + 1):
        started = time.perf_counter()
        response = client.responses.create(
            model=model,
            instructions=API_CONTRACT,
            input=prompt,
            max_output_tokens=3000,
            store=False,
            **(
                {"reasoning": {"effort": "low"}}
                if model in {"gpt-6-astra", "gpt-6-luna", "gpt-6.2-sol"}
                else {}
            ),
        )
        source = response.output_text.strip()
        row = {
            "model": model,
            "attempt": attempt,
            "seconds": round(time.perf_counter() - started, 2),
            "input_tokens": getattr(response.usage, "input_tokens", None),
            "output_tokens": getattr(response.usage, "output_tokens", None),
            "cached_input_tokens": getattr(
                getattr(response.usage, "input_tokens_details", None),
                "cached_tokens",
                0,
            ),
            "reasoning_tokens": getattr(
                getattr(response.usage, "output_tokens_details", None),
                "reasoning_tokens",
                0,
            ),
            "source": source,
        }
        try:
            if response.status != "completed":
                raise StrategyError("Response incomplete; shorten the code.")
            candidate = Strategy(source)
            check_cases(candidate, cases)
            row.update(passed=True, error="", digest=candidate.digest)
            records.append(row)
            return candidate, pd.DataFrame(records)
        except StrategyError as exc:
            row.update(passed=False, error=str(exc), digest="")
            records.append(row)
            prompt = f"{specification}\nPrevious code:\n{source}\nValidation error: {exc}\nRepair it."
    return None, pd.DataFrame(records)


def synthetic_bars(seed=42, periods=320):
    """Reproducible artificial regimes; dates are weekdays, not exchange sessions."""
    rng = np.random.default_rng(seed)
    drift = np.resize(np.repeat([0.0015, -0.0015, 0.0002, 0.001], 80), periods)
    closes = 100 * np.exp(np.cumsum(drift + rng.normal(0, 0.012, periods)))
    opens = np.r_[100.0, closes[:-1]] * np.exp(rng.normal(0, 0.003, periods))
    return pd.DataFrame(
        {"open": opens, "close": closes},
        index=pd.bdate_range("2024-01-02", periods=periods),
    )


def validate_bars(bars):
    if len(bars) < 2 or len(bars) > 10000:
        raise ValueError("Use between 2 and 10,000 bars.")
    if (
        not isinstance(bars.index, pd.DatetimeIndex)
        or not bars.index.is_monotonic_increasing
        or not bars.index.is_unique
    ):
        raise ValueError("Bars need a unique, increasing DatetimeIndex.")
    values = bars[["open", "close"]].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Prices must be finite and positive.")


def backtest(
    bars,
    strategy,
    initial_cash=10000.0,
    allocation=0.2,
    fee_bps=1.0,
    slippage_bps=5.0,
    start=30,
):
    """A close-time signal executes at the following open. No leverage/shorts.

    Whole shares, one entry until an exit signal, mark to close, no forced final
    liquidation. `start` supplies warmup without including it in the score.
    """
    validate_bars(bars)
    if (
        not all(
            math.isfinite(x) for x in (initial_cash, allocation, fee_bps, slippage_bps)
        )
        or initial_cash <= 0
        or not 0 < allocation <= 1
        or not 0 <= fee_bps <= 100
        or not 0 <= slippage_bps <= 100
        or not 1 <= start < len(bars)
    ):
        raise ValueError("Invalid backtest parameters.")
    cash, shares, rows, trades = initial_cash, 0, [], []
    fee_rate, slip = fee_bps / 10000, slippage_bps / 10000
    closes = bars.close.tolist()
    for i in range(start, len(bars)):
        desired = strategy(closes[:i])  # excludes today's close
        if type(desired) is not int or desired not in (0, 1):
            raise StrategyError("Expected integer signal 0 or 1.")
        opening, closing = bars.iloc[i][["open", "close"]]
        qty, side, fill, fee = 0, "", 0.0, 0.0
        if desired == 1 and shares == 0:
            fill = opening * (1 + slip)
            qty = math.floor(cash * allocation / (fill * (1 + fee_rate)))
            if qty:
                fee = qty * fill * fee_rate
                cash -= qty * fill + fee
                shares, side = qty, "buy"
        elif desired == 0 and shares > 0:
            fill, qty, side = opening * (1 - slip), shares, "sell"
            fee = qty * fill * fee_rate
            cash += qty * fill - fee
            shares = 0
        if side:
            trades.append(
                {
                    "date": bars.index[i],
                    "side": side,
                    "qty": qty,
                    "fill": fill,
                    "fee": fee,
                    "signal_date": bars.index[i - 1],
                }
            )
        rows.append(
            {
                "date": bars.index[i],
                "equity": cash + shares * closing,
                "cash": cash,
                "shares": shares,
                "signal": desired,
            }
        )
    curve = pd.DataFrame(rows).set_index("date")
    ledger = pd.DataFrame(
        trades, columns=["date", "side", "qty", "fill", "fee", "signal_date"]
    )
    # Include starting cash in the first return and the drawdown high-water mark.
    equity = np.r_[initial_cash, curve.equity.to_numpy()]
    returns = equity[1:] / equity[:-1] - 1
    std = returns.std(ddof=1) if len(returns) > 1 else 0
    metrics = {
        "return_pct": 100 * (equity[-1] / initial_cash - 1),
        "max_drawdown_pct": 100 * (equity / np.maximum.accumulate(equity) - 1).min(),
        "sharpe_252_rf0": np.sqrt(252) * returns.mean() / std if std > 0 else 0.0,
        "orders": len(ledger),
        "fees": float(ledger.fee.sum()),
        "final_equity": equity[-1],
    }
    return curve, ledger, metrics
