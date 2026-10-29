import operator
import uuid
from typing import Annotated, List, Optional, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
from agents.agent import Agent
from agents.deals import Deal, Opportunity
from agents.scanner_agent import ScannerAgent
from agents.ensemble_agent import EnsembleAgent
from agents.messaging_agent import MessagingAgent
from agents.planning_agent import PlanningAgent


class PlannerState(TypedDict, total=False):
    """
    Everything the graph knows while it runs. Each node reads from it and returns the parts it changes
    """

    memory: List[Opportunity]
    deals: List[Deal]
    # The reducer operator.add means: when several branches return opportunities, join their lists
    opportunities: Annotated[List[Opportunity], operator.add]
    best: Optional[Opportunity]
    worth_alerting: bool
    alerted: bool


class PriceState(TypedDict):
    """
    The small state given to each parallel branch: just the one deal it has to price
    """

    deal: Deal


class LangGraphPlanningAgent(Agent):
    """
    The planning agent rebuilt as a LangGraph graph:
    scan -> price each deal (one branch per deal) -> decide -> (optional approval) -> notify
    """

    name = "LangGraph Planning Agent"
    color = Agent.GREEN

    def __init__(self, client, use_specialist: bool = True, require_approval: bool = False, max_concurrency: int = 1):
        """
        :param client: an open QdrantClient, for the Frontier Agent's RAG search
        :param require_approval: pause before sending a message, until a person approves it
        :param max_concurrency: how many deals to price at the same time. Kept at 1 by default, because
            several simultaneous calls make Modal start extra machines for the fine-tuned model
        """
        self.log("LangGraph Planning Agent is initializing")
        self.scanner = ScannerAgent()
        self.ensemble = EnsembleAgent(client, use_specialist=use_specialist)
        self.messenger = MessagingAgent()
        self.require_approval = require_approval
        self.max_concurrency = max_concurrency
        self.graph = self.build_graph()
        self.log("LangGraph Planning Agent is ready")

    @classmethod
    def from_agents(cls, scanner, ensemble, messenger, require_approval: bool = False, max_concurrency: int = 1):
        """
        Build the planner around agents you supply, for example pretend ones for a free practice run
        """
        agent = cls.__new__(cls)
        agent.scanner, agent.ensemble, agent.messenger = scanner, ensemble, messenger
        agent.require_approval = require_approval
        agent.max_concurrency = max_concurrency
        agent.graph = agent.build_graph()
        return agent

    # The nodes: each one takes the state and returns the parts of it that it changes

    def scan(self, state: PlannerState) -> dict:
        self.log("Node 'scan': looking for deals")
        selection = self.scanner.scan(memory=state.get("memory", []))
        deals = selection.deals[:5] if selection else []
        return {"deals": deals}

    def price_deal(self, state: PriceState) -> dict:
        deal = state["deal"]
        self.log(f"Node 'price_deal': pricing a deal offered at ${deal.price:.2f}")
        estimate = self.ensemble.price(deal.product_description)
        opportunity = Opportunity(deal=deal, estimate=estimate, discount=estimate - deal.price)
        return {"opportunities": [opportunity]}

    def decide(self, state: PlannerState) -> dict:
        best = max(state["opportunities"], key=lambda opp: opp.discount)
        worth = (
            best.discount >= PlanningAgent.MIN_DISCOUNT
            and best.discount >= PlanningAgent.MIN_DISCOUNT_RATIO * best.deal.price
        )
        self.log(f"Node 'decide': best discount is ${best.discount:.2f} - {'worth' if worth else 'not worth'} an alert")
        return {"best": best, "worth_alerting": worth}

    def notify(self, state: PlannerState) -> dict:
        best = state["best"]
        if self.require_approval:
            # interrupt() pauses the whole graph here and hands this question to whoever is running it.
            # The graph only continues when it is resumed with an answer
            approved = interrupt({
                "question": "Send this deal alert?",
                "wine": best.deal.product_description,
                "price": best.deal.price,
                "estimate": round(best.estimate, 2),
                "url": best.deal.url,
            })
            if not approved:
                self.log("Node 'notify': the alert was not approved, so nothing was sent")
                return {"alerted": False}
        self.log("Node 'notify': sending the alert")
        self.messenger.alert(best)
        return {"alerted": True}

    # The routing functions: they decide which node runs next

    def route_after_scan(self, state: PlannerState):
        if not state["deals"]:
            self.log("No deals found - ending the run")
            return END
        # One Send per deal: LangGraph runs a separate price_deal branch for each
        return [Send("price_deal", {"deal": deal}) for deal in state["deals"]]

    def route_after_decide(self, state: PlannerState):
        return "notify" if state["worth_alerting"] else END

    def build_graph(self):
        graph = StateGraph(PlannerState)
        graph.add_node("scan", self.scan)
        graph.add_node("price_deal", self.price_deal)
        graph.add_node("decide", self.decide)
        graph.add_node("notify", self.notify)
        graph.add_edge(START, "scan")
        graph.add_conditional_edges("scan", self.route_after_scan, ["price_deal", END])
        graph.add_edge("price_deal", "decide")
        graph.add_conditional_edges("decide", self.route_after_decide, ["notify", END])
        graph.add_edge("notify", END)
        # The checkpointer saves the state after every step, which is what makes pausing and resuming possible
        return graph.compile(checkpointer=InMemorySaver())

    # Running the graph

    def new_config(self) -> dict:
        return {"configurable": {"thread_id": str(uuid.uuid4())}, "max_concurrency": self.max_concurrency}

    def start(self, memory: List[Opportunity] = []):
        """
        Run the graph until it finishes or pauses for approval
        :return: the config that identifies this run, and the question if it paused (otherwise None)
        """
        self.log("LangGraph Planning Agent is kicking off a run")
        config = self.new_config()
        result = self.graph.invoke({"memory": memory, "opportunities": []}, config)
        pending = result.get("__interrupt__")
        return config, (pending[0].value if pending else None)

    def resume(self, config: dict, approved: bool) -> Optional[Opportunity]:
        """
        Continue a run that paused for approval
        """
        result = self.graph.invoke(Command(resume=approved), config)
        return result["best"] if result.get("alerted") else None

    def result(self, config: dict) -> Optional[Opportunity]:
        values = self.graph.get_state(config).values
        return values.get("best") if values.get("alerted") else None

    def plan(self, memory: List[Opportunity] = []) -> Optional[Opportunity]:
        """
        Run the full workflow without stopping for approval, the same interface as the other planners
        :return: an Opportunity if one was surfaced, otherwise None
        """
        if self.require_approval:
            raise ValueError("plan() can't stop for approval; use start() and resume() instead")
        config, _ = self.start(memory)
        opportunity = self.result(config)
        self.log("LangGraph Planning Agent has completed a run")
        return opportunity
