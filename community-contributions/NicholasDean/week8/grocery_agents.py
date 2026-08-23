"""Week 8 capstone — a multi-agent grocery deal-finder (Hannaford vs Market Basket).

Mirrors the course's pattern: a PlanningAgent orchestrates specialist agents
(Scanner -> Pricers -> Reporter). Each agent is a small role around an LLM call.

NOTE: prices are gpt-4o-mini ESTIMATES (general knowledge of New England grocery prices),
not live data. A production version would plug live store APIs/flyers into the Scanner and
Pricer agents — the agent architecture stays the same.
"""
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)
client = OpenAI()
MODEL = "gpt-4o-mini"
STORES = ["Hannaford", "Market Basket"]


class Agent:
    """Base agent: a role that calls the LLM (optionally in JSON mode)."""
    name = "Agent"

    def chat(self, system, user, json_mode=False):
        kw = {"response_format": {"type": "json_object"}} if json_mode else {}
        r = client.chat.completions.create(model=MODEL, messages=[
            {"role": "system", "content": system}, {"role": "user", "content": user}], **kw)
        return r.choices[0].message.content


class ScannerAgent(Agent):
    """Produces the shopping basket. (Production: scrape weekly flyers / specials.)"""
    name = "Scanner"
    BASKET = ["1 gallon whole milk", "one dozen large eggs", "loaf of white sandwich bread",
              "2 lb bananas", "1 lb boneless chicken breast", "8 oz block cheddar cheese",
              "12 oz bag ground coffee", "1 lb butter", "64 oz orange juice", "18 oz peanut butter"]

    def run(self):
        return self.BASKET


class PricerAgent(Agent):
    """Estimates one store's prices for the basket. (Production: live store API/scrape.)"""
    name = "Pricer"

    def __init__(self, store):
        self.store = store

    def run(self, items):
        system = (f"You are a grocery pricing expert for {self.store} supermarkets in New England. "
                  "Give realistic current shelf prices in USD. Market Basket is known for low prices.")
        user = ("Return ONLY a JSON object mapping each item EXACTLY to its price as a number (USD) "
                f"at {self.store}. Items: {json.dumps(items)}")
        return json.loads(self.chat(system, user, json_mode=True))


class PlanningAgent(Agent):
    """Orchestrates the scan + both pricers, then compares to find the cheaper store per item."""
    name = "Planner"

    def run(self):
        items = ScannerAgent().run()
        prices = {s: PricerAgent(s).run(items) for s in STORES}
        rows = []
        for it in items:
            p = {s: float(prices[s].get(it, 0) or 0) for s in STORES}
            cheaper = min(STORES, key=lambda s: p[s])
            rows.append({"item": it, **p, "cheaper": cheaper, "savings": round(abs(p[STORES[0]] - p[STORES[1]]), 2)})
        totals = {s: round(sum(r[s] for r in rows), 2) for s in STORES}
        optimal = round(sum(min(r[STORES[0]], r[STORES[1]]) for r in rows), 2)  # buy each item at its cheaper store
        return {"rows": rows, "totals": totals, "optimal": optimal}


class ReportAgent(Agent):
    """Writes a short shopping recommendation from the comparison."""
    name = "Reporter"

    def run(self, plan):
        user = ("Write a concise grocery shopping recommendation (4-5 sentences) from this "
                "Hannaford vs Market Basket comparison. Say which store is cheaper overall, the "
                "total savings, and 2-3 items with the biggest difference. Data:\n" + json.dumps(plan))
        return self.chat("You are a frugal shopping assistant.", user)


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    plan = PlanningAgent().run()
    for r in plan["rows"]:
        print(f"  {r['item']:<32} H ${r['Hannaford']:>5.2f}  MB ${r['Market Basket']:>5.2f}  -> {r['cheaper']}")
    print("totals:", plan["totals"], "| optimal split: $", plan["optimal"])
    print("\n" + ReportAgent().run(plan))
