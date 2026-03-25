import json
import os
from typing import List
from openai import OpenAI
from agents.agent import Agent
from agents.ensemble_agent import EnsembleAgent
from agents.resources import ResourceOpportunity, ScannedResource
from agents.scanner_agent import ScannerAgent


class AutonomousPlanningAgent(Agent):
    name = "Autonomous Planning Agent"
    color = Agent.GREEN
    MODEL = "openai/gpt-4o-mini"

    def __init__(self):
        self.log("Autonomous Planning Agent is initializing")
        self.scanner = ScannerAgent()
        self.ensemble = EnsembleAgent()
        self.model = os.getenv("OPENROUTER_MODEL", self.MODEL)
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        openrouter_base_url = os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ).strip()

        self.openai = OpenAI(api_key=openrouter_key, base_url=openrouter_base_url)
        self.memory: List[ResourceOpportunity] = []
        self.topic = "llm agents"
        self.scored_candidates: List[ResourceOpportunity] = []
        self.log("Autonomous Planning Agent is ready")

    def scan_for_resources(self) -> str:
        self.log("Tool call: scan_for_resources")
        memory_urls = [item.resource.url for item in self.memory]
        result = self.scanner.scan(topic=self.topic, memory_urls=memory_urls)
        return result.model_dump_json()

    def estimate_resource_quality(self, title: str, url: str, source: str, snippet: str) -> str:
        self.log("Tool call: estimate_resource_quality")
        resource = ScannedResource(title=title, url=url, source=source, snippet=snippet)
        scored = self.ensemble.score(resource=resource, topic=self.topic)
        self.scored_candidates.append(scored)
        return scored.model_dump_json()

    scan_function = {
        "name": "scan_for_resources",
        "description": "Scan online sources and return candidate learning resources in JSON",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    }
    estimate_function = {
        "name": "estimate_resource_quality",
        "description": "Estimate a quality score for one resource candidate and return ResourceOpportunity JSON",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "url": {"type": "string"},
                "source": {"type": "string"},
                "snippet": {"type": "string"},
            },
            "required": ["title", "url", "source", "snippet"],
            "additionalProperties": False,
        },
    }

    def get_tools(self) -> List[dict]:
        return [
            {"type": "function", "function": self.scan_function},
            {"type": "function", "function": self.estimate_function},
        ]

    def _mapping(self):
        return {
            "scan_for_resources": self.scan_for_resources,
            "estimate_resource_quality": self.estimate_resource_quality,
        }

    def handle_tool_call(self, message) -> List[dict]:
        results = []
        mapping = self._mapping()
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            tool = mapping.get(name)
            output = tool(**args) if tool else ""
            if not isinstance(output, str):
                output = json.dumps(output)
            results.append(
                {"role": "tool", "tool_call_id": tool_call.id, "content": output}
            )
        return results

    @staticmethod
    def _top5(opportunities: List[ResourceOpportunity]) -> List[ResourceOpportunity]:
        opportunities.sort(key=lambda item: item.estimated_quality, reverse=True)
        return opportunities[:5]

    def plan(
        self, topic: str, memory: List[ResourceOpportunity]
    ) -> List[ResourceOpportunity]:
        self.log("Autonomous Planning Agent is kicking off a run")
        self.topic = topic
        self.memory = memory
        self.scored_candidates = []

        system_message = (
            "You are an autonomous resource scout. Use tools in a loop: "
            "first call scan_for_resources once, then call estimate_resource_quality for each promising candidate. "
            "Estimate at least 5 candidates and at most 10 candidates. When done, respond with DONE."
        )
        user_message = f"Find the top learning resources for this topic: {topic}"
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

        done = False
        iterations = 0
        while not done and iterations < 10:
            iterations += 1
            response = self.openai.chat.completions.create(
                model=self.model, messages=messages, tools=self.get_tools()
            )
            choice = response.choices[0]
            if choice.finish_reason == "tool_calls":
                message = choice.message
                tool_results = self.handle_tool_call(message)
                messages.append(message)
                messages.extend(tool_results)
            else:
                done = True
        self.log(f"Autonomous Planning Agent completed with: {response.choices[0].message.content}")
        return self._top5(self.scored_candidates)
