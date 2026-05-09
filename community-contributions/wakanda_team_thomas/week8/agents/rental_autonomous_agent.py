import json
from openai import OpenAI
from agents.agent import Agent
from agents.rental_deals import RentalDeal, RentalOpportunity
from agents.rental_scanner_agent import RentalScannerAgent
from agents.rental_ensemble_agent import RentalEnsembleAgent
from agents.rental_messaging_agent import RentalMessagingAgent


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "scan_rental_listings",
            "description": "Scan rental listings across New York, Lagos, and Nairobi to find available properties.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_fair_rent",
            "description": "Estimate the true fair market rent for a rental property using an ensemble of AI models.",
            "parameters": {
                "type": "object",
                "properties": {
                    "deal_index": {
                        "type": "integer",
                        "description": "Index of the deal in the scanned listings to estimate.",
                    }
                },
                "required": ["deal_index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "alert_user_of_deal",
            "description": "Send a push notification to the user about a rental deal worth pursuing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "deal_index": {
                        "type": "integer",
                        "description": "Index of the deal to alert the user about.",
                    }
                },
                "required": ["deal_index"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are an autonomous rental deal hunting agent. Your job is to:
1. Scan rental listings across New York, Lagos, and Nairobi
2. Estimate the fair market rent for promising listings
3. Alert the user about deals where the listed rent is significantly below fair market value

Use the tools provided to accomplish this. A good deal has monthly savings of at least $50.
Do not alert the user about the same deal more than once."""


class RentalAutonomousAgent(Agent):
    """Self-directed agent that uses OpenAI function calling to orchestrate deal hunting."""

    name = "Autonomous"
    color = "red"

    def __init__(self, scanner: RentalScannerAgent, ensemble: RentalEnsembleAgent, messenger: RentalMessagingAgent):
        self.client = OpenAI()
        self.scanner = scanner
        self.ensemble = ensemble
        self.messenger = messenger
        self.deals: list[RentalDeal] = []
        self.opportunities: list[RentalOpportunity] = []
        self.alerted: set[int] = set()

    def run(self) -> list[RentalOpportunity]:
        self.log("Starting autonomous deal hunting...")
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.append({"role": "user", "content": "Find the best rental deals and alert me about any bargains."})

        while True:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=TOOLS,
            )

            choice = response.choices[0]

            if choice.finish_reason == "stop":
                self.log("Agent finished.")
                if choice.message.content:
                    self.log(f"Summary: {choice.message.content}")
                break

            if choice.finish_reason == "tool_calls":
                messages.append(choice.message)
                for tool_call in choice.message.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    self.log(f"Tool call: {name}({args})")

                    result = self._execute_tool(name, args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })

        return self.opportunities

    def _execute_tool(self, name: str, args: dict) -> str:
        if name == "scan_rental_listings":
            self.deals = self.scanner.scan()
            summaries = [
                f"{i}: {d.title} — ${d.rent:,.2f}/mo"
                for i, d in enumerate(self.deals)
            ]
            return f"Found {len(self.deals)} deals:\n" + "\n".join(summaries)

        elif name == "estimate_fair_rent":
            idx = args.get("deal_index", 0)
            if idx < 0 or idx >= len(self.deals):
                return f"Invalid deal index: {idx}"
            deal = self.deals[idx]
            estimate = self.ensemble.estimate(deal)
            savings = estimate - deal.rent
            opp = RentalOpportunity(
                deal=deal,
                estimated_fair_rent=estimate,
                monthly_savings=max(savings, 0),
            )
            self.opportunities.append(opp)
            return (
                f"Deal: {deal.title}\n"
                f"Listed: ${deal.rent:,.2f}/mo\n"
                f"Estimated fair rent: ${estimate:,.2f}/mo\n"
                f"Monthly savings: ${savings:,.2f}"
            )

        elif name == "alert_user_of_deal":
            idx = args.get("deal_index", 0)
            if idx in self.alerted:
                return "Already alerted for this deal."
            matching = [o for o in self.opportunities if o.deal == self.deals[idx]]
            if not matching:
                return "No estimate found for this deal. Run estimate_fair_rent first."
            self.messenger.alert(matching[0])
            self.alerted.add(idx)
            return f"Alert sent for: {self.deals[idx].title}"

        return f"Unknown tool: {name}"
