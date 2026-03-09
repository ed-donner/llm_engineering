from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import List


ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
MEMORY_PATH = ARTIFACTS_DIR / "memory.json"


@dataclass
class Deal:
    title: str
    summary: str
    category: str
    listed_price: float
    url: str


@dataclass
class Opportunity:
    deal: Deal
    specialist_estimate: float
    rag_estimate: float
    ensemble_estimate: float

    @property
    def discount(self) -> float:
        return self.ensemble_estimate - self.deal.listed_price


def ensure_artifacts() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    if not MEMORY_PATH.exists():
        MEMORY_PATH.write_text("[]", encoding="utf-8")


def read_memory() -> list[dict]:
    ensure_artifacts()
    return json.loads(MEMORY_PATH.read_text(encoding="utf-8"))


def write_memory(rows: list[dict]) -> None:
    ensure_artifacts()
    MEMORY_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")


class SpecialistAgent:
    """
    Day 1 style specialist pricer.
    If MODAL_ENDPOINT is set, this class can be extended to call a deployed endpoint.
    For this contribution we keep a deterministic local estimate so the project runs anywhere.
    """

    CATEGORY_BASE = {
        "Electronics": 180.0,
        "Home": 95.0,
        "Tools": 120.0,
        "Toys": 55.0,
    }

    def estimate(self, deal: Deal) -> float:
        text = f"{deal.title} {deal.summary}".lower()
        base = self.CATEGORY_BASE.get(deal.category, 100.0)
        if re.search(r"\bpro\b", text) or re.search(r"\bpremium\b", text):
            base += 70
        if re.search(r"\bmini\b", text) or re.search(r"\bcompact\b", text):
            base -= 25
        if re.search(r"\bbundle\b", text):
            base += 40
        if re.search(r"\bwireless\b", text):
            base += 20
        return round(max(10.0, base), 2)


class RAGAgent:
    """
    Day 2 style local retrieval estimate using lexical overlap
    against a small reference catalog.
    """

    def __init__(self) -> None:
        self.reference_catalog = [
            ("Wireless ANC headphones with travel case", 229.0, "Electronics"),
            ("Compact mechanical keyboard with RGB lights", 119.0, "Electronics"),
            ("Cordless drill kit with 2 batteries", 149.0, "Tools"),
            ("Non-stick cookware set 10-piece", 89.0, "Home"),
            ("Smart air fryer oven 6 quart", 129.0, "Home"),
            ("STEM robotics kit for kids", 69.0, "Toys"),
            ("Portable bluetooth speaker waterproof", 99.0, "Electronics"),
            ("Ergonomic office chair with lumbar support", 199.0, "Home"),
        ]

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    def estimate(self, deal: Deal) -> float:
        deal_tokens = self._tokens(f"{deal.title} {deal.summary}")
        scored = []
        for description, price, category in self.reference_catalog:
            cat_boost = 1.3 if category == deal.category else 1.0
            overlap = len(deal_tokens.intersection(self._tokens(description)))
            scored.append((overlap * cat_boost, price))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [price for score, price in scored[:3] if score > 0]
        estimate = mean(top) if top else mean(price for _, price, _ in self.reference_catalog)
        return round(float(estimate), 2)


class EnsembleAgent:
    """
    Day 2 ensemble.
    """

    def combine(self, specialist_estimate: float, rag_estimate: float) -> float:
        return round(0.55 * specialist_estimate + 0.45 * rag_estimate, 2)


class ScannerAgent:
    """
    Day 3 scanner.
    """

    def scan(self, limit: int = 8) -> list[Deal]:
        candidates = [
            Deal(
                title="Premium wireless ANC headphones bundle",
                summary="Over-ear bluetooth headphones with ANC and hard case bundle.",
                category="Electronics",
                listed_price=129.99,
                url="https://example.com/deal/headphones-bundle",
            ),
            Deal(
                title="Compact cordless drill kit",
                summary="Drill driver with charger and two lithium batteries.",
                category="Tools",
                listed_price=84.50,
                url="https://example.com/deal/drill-kit",
            ),
            Deal(
                title="Smart 6qt air fryer mini",
                summary="Countertop air fryer with app support and presets.",
                category="Home",
                listed_price=79.99,
                url="https://example.com/deal/air-fryer-mini",
            ),
            Deal(
                title="Kids robotics starter kit",
                summary="STEM learning kit with sensors and coding guide.",
                category="Toys",
                listed_price=39.00,
                url="https://example.com/deal/robotics-kit",
            ),
            Deal(
                title="Mechanical keyboard pro wireless",
                summary="Low-profile wireless keyboard with tactile switches.",
                category="Electronics",
                listed_price=74.99,
                url="https://example.com/deal/keyboard-pro",
            ),
        ]
        random.seed(42)
        random.shuffle(candidates)
        return candidates[: max(1, min(limit, len(candidates)))]


class MessagingAgent:
    """
    Day 3 notification agent.
    """

    def alert(self, opp: Opportunity) -> str:
        message = (
            f"DEAL ALERT: {opp.deal.title} | listed=${opp.deal.listed_price:.2f} | "
            f"estimated=${opp.ensemble_estimate:.2f} | potential value=${opp.discount:.2f} | {opp.deal.url}"
        )
        print(message)
        return message


class PlanningAgent:
    """
    Day 4 planner.
    """

    def __init__(self, specialist: SpecialistAgent, rag: RAGAgent, ensemble: EnsembleAgent):
        self.specialist = specialist
        self.rag = rag
        self.ensemble = ensemble
        self.messenger = MessagingAgent()

    def rank(self, deals: list[Deal]) -> list[Opportunity]:
        opportunities: list[Opportunity] = []
        for deal in deals:
            spec = self.specialist.estimate(deal)
            rag = self.rag.estimate(deal)
            ens = self.ensemble.combine(spec, rag)
            opportunities.append(
                Opportunity(
                    deal=deal,
                    specialist_estimate=spec,
                    rag_estimate=rag,
                    ensemble_estimate=ens,
                )
            )
        opportunities.sort(key=lambda opp: opp.discount, reverse=True)
        return opportunities

    def plan_and_notify(self, deals: list[Deal], top_k: int = 2) -> list[Opportunity]:
        ranked = self.rank(deals)
        for opp in ranked[:top_k]:
            if opp.discount > 20:
                self.messenger.alert(opp)
        return ranked


class Week8CapstoneFramework:
    """
    Day 5 framework and run loop.
    """

    def __init__(self):
        self.scanner = ScannerAgent()
        self.planner = PlanningAgent(SpecialistAgent(), RAGAgent(), EnsembleAgent())

    def run_once(self, limit: int = 5) -> list[Opportunity]:
        deals = self.scanner.scan(limit=limit)
        ranked = self.planner.plan_and_notify(deals, top_k=2)
        rows = read_memory()
        for opp in ranked:
            rows.append(
                {
                    "title": opp.deal.title,
                    "listed_price": opp.deal.listed_price,
                    "specialist_estimate": opp.specialist_estimate,
                    "rag_estimate": opp.rag_estimate,
                    "ensemble_estimate": opp.ensemble_estimate,
                    "discount": opp.discount,
                    "url": opp.deal.url,
                }
            )
        write_memory(rows[-50:])
        return ranked


def build_eval_set() -> list[tuple[Deal, float]]:
    return [
        (
            Deal(
                title="Wireless ANC headphones premium",
                summary="Bluetooth headphones with active noise cancellation.",
                category="Electronics",
                listed_price=149.0,
                url="https://example.com/eval/1",
            ),
            225.0,
        ),
        (
            Deal(
                title="Compact cordless drill kit",
                summary="Power drill with 2 batteries and charger.",
                category="Tools",
                listed_price=99.0,
                url="https://example.com/eval/2",
            ),
            145.0,
        ),
        (
            Deal(
                title="Smart air fryer mini",
                summary="Countertop fryer with touch panel.",
                category="Home",
                listed_price=85.0,
                url="https://example.com/eval/3",
            ),
            130.0,
        ),
        (
            Deal(
                title="Kids robotics starter kit bundle",
                summary="STEM education pack for beginners.",
                category="Toys",
                listed_price=49.0,
                url="https://example.com/eval/4",
            ),
            72.0,
        ),
    ]


def mae(y_true: list[float], y_pred: list[float]) -> float:
    return sum(abs(a - b) for a, b in zip(y_true, y_pred)) / max(1, len(y_true))


def rmse(y_true: list[float], y_pred: list[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(y_true, y_pred)) / max(1, len(y_true)))


def command_plan(_args: argparse.Namespace) -> None:
    plan = {
        "day1": "Specialist pricing agent with optional remote deployment hook.",
        "day2": "RAG estimate and ensemble combination.",
        "day3": "Scanner and notifier for candidate deals.",
        "day4": "Planning agent for ranking and autonomous notification decisions.",
        "day5": "Framework orchestration and optional Gradio deployment.",
        "deliverables": [
            "week8_capstone_multi_agent.py",
            "week8_capstone_multi_agent.ipynb",
            "artifacts/memory.json",
        ],
    }
    print(json.dumps(plan, indent=2))


def command_build(_args: argparse.Namespace) -> None:
    ensure_artifacts()
    print(f"Artifacts initialized at: {ARTIFACTS_DIR}")


def command_scan(args: argparse.Namespace) -> None:
    framework = Week8CapstoneFramework()
    deals = framework.scanner.scan(limit=args.limit)
    print(json.dumps([asdict(d) for d in deals], indent=2))


def command_run_once(args: argparse.Namespace) -> None:
    framework = Week8CapstoneFramework()
    ranked = framework.run_once(limit=args.limit)
    payload = [
        {
            "title": opp.deal.title,
            "listed_price": opp.deal.listed_price,
            "specialist_estimate": opp.specialist_estimate,
            "rag_estimate": opp.rag_estimate,
            "ensemble_estimate": opp.ensemble_estimate,
            "discount": opp.discount,
            "url": opp.deal.url,
        }
        for opp in ranked
    ]
    print(json.dumps(payload, indent=2))


def command_evaluate(_args: argparse.Namespace) -> None:
    specialist = SpecialistAgent()
    rag = RAGAgent()
    ens = EnsembleAgent()
    eval_data = build_eval_set()
    y_true = [target for _, target in eval_data]
    y_spec = [specialist.estimate(deal) for deal, _ in eval_data]
    y_rag = [rag.estimate(deal) for deal, _ in eval_data]
    y_ens = [ens.combine(s, r) for s, r in zip(y_spec, y_rag)]
    result = {
        "specialist_mae": round(mae(y_true, y_spec), 3),
        "rag_mae": round(mae(y_true, y_rag), 3),
        "ensemble_mae": round(mae(y_true, y_ens), 3),
        "ensemble_rmse": round(rmse(y_true, y_ens), 3),
    }
    print(json.dumps(result, indent=2))


def command_deploy(_args: argparse.Namespace) -> None:
    try:
        import gradio as gr
    except ModuleNotFoundError:
        raise SystemExit("gradio is required for deploy. Install it in your environment first.")

    specialist = SpecialistAgent()
    rag = RAGAgent()
    ens = EnsembleAgent()

    def estimate_product(title: str, summary: str, category: str, listed_price: float):
        deal = Deal(
            title=title,
            summary=summary,
            category=category,
            listed_price=float(listed_price),
            url="https://local-ui",
        )
        spec = specialist.estimate(deal)
        rag_est = rag.estimate(deal)
        final = ens.combine(spec, rag_est)
        discount = final - deal.listed_price
        return (
            f"${spec:.2f}",
            f"${rag_est:.2f}",
            f"${final:.2f}",
            f"${discount:.2f}",
        )

    demo = gr.Interface(
        fn=estimate_product,
        inputs=[
            gr.Textbox(label="Title", value="Wireless ANC headphones bundle"),
            gr.Textbox(label="Summary", value="Bluetooth headphones with travel case and ANC."),
            gr.Dropdown(
                label="Category",
                choices=["Electronics", "Home", "Tools", "Toys"],
                value="Electronics",
            ),
            gr.Number(label="Listed price", value=129.99),
        ],
        outputs=[
            gr.Textbox(label="Specialist estimate"),
            gr.Textbox(label="RAG estimate"),
            gr.Textbox(label="Ensemble estimate"),
            gr.Textbox(label="Potential value"),
        ],
        title="Week 8 Capstone - BernardUdo",
        description="Multi-agent price estimation demo (specialist + RAG + ensemble).",
    )
    preferred_port = int(os.getenv("WEEK8_GRADIO_PORT", "7868"))
    candidate_ports = [preferred_port] + list(range(7869, 7881))
    last_error: Exception | None = None
    for port in candidate_ports:
        try:
            demo.launch(server_name="127.0.0.1", server_port=port, share=False)
            return
        except Exception as exc:
            last_error = exc
    raise SystemExit(f"Unable to launch Gradio on ports {candidate_ports}: {last_error}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Week 8 multi-agent capstone contribution")
    sub = parser.add_subparsers(dest="command", required=True)

    p_plan = sub.add_parser("plan", help="Print day-by-day plan and deliverables")
    p_plan.set_defaults(func=command_plan)

    p_build = sub.add_parser("build", help="Initialize artifacts")
    p_build.set_defaults(func=command_build)

    p_scan = sub.add_parser("scan", help="Scan candidate deals")
    p_scan.add_argument("--limit", type=int, default=5)
    p_scan.set_defaults(func=command_scan)

    p_run = sub.add_parser("run-once", help="Run one end-to-end cycle")
    p_run.add_argument("--limit", type=int, default=5)
    p_run.set_defaults(func=command_run_once)

    p_eval = sub.add_parser("evaluate", help="Run quick offline metrics")
    p_eval.set_defaults(func=command_evaluate)

    p_deploy = sub.add_parser("deploy", help="Launch local Gradio UI")
    p_deploy.set_defaults(func=command_deploy)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
