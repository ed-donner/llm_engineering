from typing import Optional, List, Set
from agents.agent import Agent
from agents.models import Article, Opportunity
from agents.scanner_agent import ScannerAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.analysis_agent import AnalysisAgent
from agents.messenger_agent import MessengerAgent
from openai import OpenAI
import json


class PlanningAgent(Agent):

    name = "Planning Agent"
    color = Agent.GREEN
    MODEL = "gpt-4.1-mini"

    def __init__(self, collection):
        self.log("Initializing all agents")
        self.scanner = ScannerAgent()
        self.knowledge = KnowledgeAgent(collection)
        self.analysis = AnalysisAgent(self.knowledge)
        self.messenger = MessengerAgent()
        self.openai = OpenAI()
        self.seen_urls: Set[str] = set()
        self.processed_urls: Set[str] = set()
        self.opportunity: Optional[Opportunity] = None
        self.log("All agents ready")

    def scan_for_news(self) -> str:
        self.log("Tool call: scan_for_news")
        result = self.scanner.scan(seen_urls=self.seen_urls)
        return result.model_dump_json() if result else "No new articles found"

    def analyze_article(self, title: str, summary: str, url: str, source: str = "") -> str:
        self.log(f"Tool call: analyze_article -> {title[:40]}...")
        self.processed_urls.add(url)
        score = self.analysis.analyze(title, summary, url)
        return json.dumps({"title": title, "importance": score, "url": url})

    def send_alert(self, title: str, summary: str, importance_score: float, url: str) -> str:
        if self.opportunity:
            self.log("Alert already sent this cycle - skipping duplicate")
            return "Already alerted this cycle"
        self.log(f"Tool call: send_alert -> {title[:40]}...")
        self.messenger.notify(title, summary, importance_score, url)
        article = Article(title=title, url=url, summary=summary, source="")
        self.opportunity = Opportunity(
            article=article, importance=importance_score, alerted=True
        )
        return "Alert sent successfully"

    scan_fn = {
        "name": "scan_for_news",
        "description": "Scan tech news feeds (Hacker News, TechCrunch) for the latest stories",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    }

    analyze_fn = {
        "name": "analyze_article",
        "description": "Analyze a tech article's importance using RAG context and ML scoring. Returns an importance score 0-10.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Article title"},
                "summary": {"type": "string", "description": "Article summary"},
                "url": {"type": "string", "description": "Article URL"},
                "source": {"type": "string", "description": "Article source"},
            },
            "required": ["title", "summary", "url"],
            "additionalProperties": False,
        },
    }

    alert_fn = {
        "name": "send_alert",
        "description": "Send a push notification about the single most important story. Only call once per cycle.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Article title"},
                "summary": {"type": "string", "description": "Brief summary"},
                "importance_score": {
                    "type": "number",
                    "description": "Importance score 0-10",
                },
                "url": {"type": "string", "description": "Article URL"},
            },
            "required": ["title", "summary", "importance_score", "url"],
            "additionalProperties": False,
        },
    }

    def get_tools(self):
        return [
            {"type": "function", "function": self.scan_fn},
            {"type": "function", "function": self.analyze_fn},
            {"type": "function", "function": self.alert_fn},
        ]

    def handle_tool_call(self, message):
        mapping = {
            "scan_for_news": self.scan_for_news,
            "analyze_article": self.analyze_article,
            "send_alert": self.send_alert,
        }
        results = []
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            fn = mapping.get(name)
            result = fn(**args) if fn else ""
            results.append(
                {"role": "tool", "content": result, "tool_call_id": tool_call.id}
            )
        return results

    system_message = (
        "You are a tech news intelligence agent. Your job is to find the most important "
        "tech stories and alert the user about truly significant news.\n"
        "Steps:\n"
        "1. Scan for the latest news\n"
        "2. Analyze each article's importance\n"
        "3. Send an alert for the single most important story scoring >= 6/10\n"
        "If nothing scores above 6, do NOT send an alert. Reply OK when done."
    )

    user_message = (
        "Scan for the latest tech news, analyze each article's importance, "
        "and alert me about the most significant story if any."
    )

    def plan(self, seen_urls: Optional[Set[str]] = None) -> Optional[Opportunity]:
        self.log("Starting autonomous planning cycle")
        self.seen_urls = seen_urls or set()
        self.processed_urls = set()
        self.opportunity = None

        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": self.user_message},
        ]

        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model=self.MODEL, messages=messages, tools=self.get_tools()
            )
            if response.choices[0].finish_reason == "tool_calls":
                message = response.choices[0].message
                results = self.handle_tool_call(message)
                messages.append(message)
                messages.extend(results)
            else:
                done = True

        reply = response.choices[0].message.content
        self.log(f"Planning cycle complete: {reply}")
        return self.opportunity
