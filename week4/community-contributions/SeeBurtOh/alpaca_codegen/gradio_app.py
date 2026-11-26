"""Local Gradio front end for the same strategy engine and paper broker."""

import json
from functools import wraps

import gradio as gr
import pandas as pd
from openai import OpenAI

from strategy_lab import (
    DEFAULT_SPEC,
    REFERENCE_SOURCE,
    Strategy,
    StrategyError,
    acceptance_cases,
    backtest,
    check_cases,
    generate_strategy,
    synthetic_bars,
)


def ui_action(fn):
    @wraps(fn)
    def wrapped(*args):
        try:
            return fn(*args)
        except (StrategyError, ValueError) as exc:
            raise gr.Error(str(exc)) from None
        except Exception as exc:
            # Provider exceptions may contain credential fragments; keep them private.
            status = getattr(exc, "status_code", None)
            raise gr.Error(
                f"{type(exc).__name__} (HTTP {status or 'n/a'}). Check the service connection and credentials."
            ) from None

    return wrapped


def read_cases(text):
    cases = json.loads(text)
    if not isinstance(cases, list) or not 1 <= len(cases) <= 50:
        raise ValueError("Provide 1–50 [closing_prices, expected_signal] examples.")
    for case in cases:
        if (
            not isinstance(case, list)
            or len(case) != 2
            or not isinstance(case[0], list)
            or len(case[0]) > 200
            or type(case[1]) is not int
            or case[1] not in (0, 1)
        ):
            raise ValueError(
                "Each example needs a price list (up to 200 prices) and integer 0 or 1."
            )
    return cases


def checked_strategy(source, cases_text):
    strategy = Strategy(source)
    check_cases(strategy, read_cases(cases_text))
    return strategy


def paper_connection(enabled):
    if not enabled:
        raise ValueError("Enable paper-account access first.")
    from paper_broker import PaperBroker

    return PaperBroker()


@ui_action
def generate(spec, model, cases_text):
    strategy, log = generate_strategy(
        OpenAI(timeout=60, max_retries=0), model, spec, read_cases(cases_text)
    )
    if strategy is None:
        return (
            "",
            log.drop(columns="source"),
            "Generation failed its checks. Revise the specification or examples.",
        )
    return (
        strategy.source,
        log.drop(columns="source"),
        f"Generated with {model}; example checks passed. Run a backtest next.",
    )


@ui_action
def evaluate(source, cases_text, data_source, symbol, enabled):
    strategy = checked_strategy(source, cases_text)
    if data_source == "Alpaca IEX":
        end = pd.Timestamp.now(tz="America/New_York").normalize()
        bars = paper_connection(enabled).bars(
            symbol.strip().upper(), end - pd.Timedelta(days=730), end
        )
    else:
        bars = synthetic_bars()
    cut = int(len(bars) * 0.65)
    if cut < 40 or len(bars) - cut < 20:
        raise ValueError("Not enough bars for development and holdout periods.")
    curve, ledger, metrics = backtest(bars, strategy, start=cut)
    benchmark, _, baseline = backtest(bars, lambda closes: 1, start=cut)
    chart = pd.concat(
        [
            pd.DataFrame(
                {
                    "date": curve.index,
                    "equity": curve.equity.to_numpy(),
                    "strategy": "Current strategy",
                }
            ),
            pd.DataFrame(
                {
                    "date": benchmark.index,
                    "equity": benchmark.equity.to_numpy(),
                    "strategy": "Buy and hold",
                }
            ),
        ],
        ignore_index=True,
    )
    scores = pd.DataFrame(
        [
            {"strategy": "Current strategy", **metrics},
            {"strategy": "Buy and hold", **baseline},
        ]
    )
    return (
        scores.round(4),
        chart,
        ledger,
        f"Checks passed. Holdout used {data_source}; both accounts started with $10,000.",
    )


@ui_action
def connect(enabled):
    return paper_connection(enabled).connection_status()


@ui_action
def preview(source, cases_text, symbol, budget, enabled):
    strategy = checked_strategy(source, cases_text)
    symbol = symbol.strip().upper()
    plan = paper_connection(enabled).preview(strategy, symbol, max_notional=budget)
    snapshot = {
        "source": source,
        "cases": cases_text,
        "symbol": symbol,
        "budget": budget,
        "plan": plan,
    }
    return plan, snapshot, False


@ui_action
def submit(source, cases_text, symbol, budget, enabled, reviewed, snapshot):
    if not reviewed or not snapshot:
        raise ValueError("Preview an order and check that it has been reviewed first.")
    if any(
        snapshot.get(k) != v
        for k, v in {
            "source": source,
            "cases": cases_text,
            "symbol": symbol.strip().upper(),
            "budget": budget,
        }.items()
    ):
        raise ValueError("Inputs changed. Create a new preview.")
    strategy = checked_strategy(source, cases_text)
    result = paper_connection(enabled).submit(
        strategy,
        snapshot["plan"],
        symbol=snapshot["symbol"],
        max_notional=budget,
    )
    return result, result["client_order_id"], None, False, None


@ui_action
def refresh(enabled, client_id):
    if not client_id:
        raise ValueError("No order has been submitted in this session.")
    return paper_connection(enabled).order_status(client_id)


def build_ui(initial_source=REFERENCE_SOURCE, model="gpt-6-luna"):
    with gr.Blocks(title="Strategy Code Lab", analytics_enabled=False) as app:
        gr.Markdown(
            "# Strategy Code Lab\nGenerate a Python strategy, test it, then preview an Alpaca paper order. Generation uses paid API calls."
        )
        with gr.Row():
            model_box = gr.Dropdown(
                ["gpt-6-luna", "gpt-6.2-sol", "gpt-6-astra"], value=model, label="Model"
            )
            symbol = gr.Textbox(value="AAPL", label="Stock symbol")
            enabled = gr.Checkbox(
                value=False, label="Enable Alpaca paper-account access"
            )
        with gr.Tab("1. Strategy and backtest"):
            spec = gr.Textbox(value=DEFAULT_SPEC, lines=4, label="Strategy description")
            with gr.Accordion(
                "Expected behavior examples — update when changing the rule", open=False
            ):
                cases = gr.Code(
                    value=json.dumps(acceptance_cases()),
                    language="json",
                    label="[prices, expected signal] examples",
                )
            with gr.Row():
                generate_button = gr.Button(
                    "Generate strategy (paid API)", variant="primary"
                )
                reference_button = gr.Button("Load offline reference")
            source = gr.Code(
                value=initial_source,
                language="python",
                label="Strategy code — editable",
                lines=12,
                interactive=True,
            )
            status = gr.Markdown("Code loaded. Run the backtest to check it.")
            attempts = gr.Dataframe(label="Generation attempts", interactive=False)
            with gr.Row():
                data_source = gr.Dropdown(
                    ["Synthetic", "Alpaca IEX"],
                    value="Synthetic",
                    label="Backtest data",
                )
                test_button = gr.Button("Validate and backtest")
            scores = gr.Dataframe(label="Holdout metrics", interactive=False)
            chart = gr.LinePlot(
                x="date",
                y="equity",
                color="strategy",
                title="Holdout account value",
                y_title="Equity ($)",
            )
            ledger = gr.Dataframe(label="Simulated orders", interactive=False)
        with gr.Tab("2. Alpaca paper trading"):
            gr.Markdown(
                "Use a dedicated paper account. A HOLD response is normal if the session is closed or the position already matches the strategy."
            )
            connect_button = gr.Button("Check paper connection")
            connection = gr.JSON(label="Connection status")
            budget = gr.Slider(
                50,
                1000,
                value=1000,
                step=50,
                label="Maximum entry budget ($ of paper money)",
            )
            preview_button = gr.Button("Preview paper order")
            plan = gr.JSON(label="Order preview")
            reviewed = gr.Checkbox(value=False, label="I reviewed this paper order")
            submit_button = gr.Button("Submit reviewed paper order")
            refresh_button = gr.Button("Refresh order status")
            result = gr.JSON(label="Order status — acceptance does not mean filled")
        snapshot, last_order = gr.State(None), gr.State("")
        generate_button.click(
            generate, [spec, model_box, cases], [source, attempts, status]
        )
        reference_button.click(
            lambda: (
                REFERENCE_SOURCE,
                DEFAULT_SPEC,
                json.dumps(acceptance_cases()),
                "Authored reference loaded; no model called.",
            ),
            outputs=[source, spec, cases, status],
        )
        test_button.click(
            evaluate,
            [source, cases, data_source, symbol, enabled],
            [scores, chart, ledger, status],
        )
        paper_queue = {"concurrency_id": "paper-account", "concurrency_limit": 1}
        connect_button.click(connect, enabled, connection, **paper_queue)

        def clear():
            return None, None, False

        for component in [source, cases, symbol, budget, enabled]:
            component.change(clear, outputs=[plan, snapshot, reviewed], queue=False)
        for component in [source, cases, data_source, symbol, enabled]:
            component.change(
                lambda: (None, None, None), outputs=[scores, chart, ledger], queue=False
            )
        preview_button.click(
            clear, outputs=[plan, snapshot, reviewed], queue=False
        ).then(
            preview,
            [source, cases, symbol, budget, enabled],
            [plan, snapshot, reviewed],
            **paper_queue,
        )
        submit_button.click(
            submit,
            [source, cases, symbol, budget, enabled, reviewed, snapshot],
            [result, last_order, snapshot, reviewed, plan],
            **paper_queue,
        )
        refresh_button.click(refresh, [enabled, last_order], result, **paper_queue)
    return app
