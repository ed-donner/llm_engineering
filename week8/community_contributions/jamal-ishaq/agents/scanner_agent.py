from typing import List
from urllib.parse import urlparse

try:
    import feedparser
except ImportError:  # pragma: no cover - fallback for minimal local setup
    feedparser = None

from agents.agent import Agent
from agents.resources import ResourceSelection, ScannedResource


FALLBACK_RESOURCES = [
    ScannedResource(
        title="OpenAI Evals Design Guide",
        url="https://platform.openai.com/docs/guides/evals",
        source="openai.com",
        snippet="A practical guide for building evaluation datasets and pass/fail criteria for LLM systems.",
    ),
    ScannedResource(
        title="LangChain Agent Executor Concepts",
        url="https://python.langchain.com/docs/concepts/agents/",
        source="langchain.com",
        snippet="Core concepts behind tool-using agents, planning, and execution loops.",
    ),
    ScannedResource(
        title="DSPy: Programming Rather Than Prompting",
        url="https://github.com/stanfordnlp/dspy",
        source="github.com",
        snippet="Framework for declarative LM programming and optimization workflows.",
    ),
    ScannedResource(
        title="Awesome LLM Evaluation Repositories",
        url="https://github.com/topics/llm-evaluation",
        source="github.com",
        snippet="Curated repositories covering benchmarks, judges, and evaluation pipelines.",
    ),
]


class ScannerAgent(Agent):
    name = "Scanner Agent"
    color = Agent.CYAN

    FEEDS = [
        "https://hnrss.org/newest?q=llm+agents",
        "https://hnrss.org/newest?q=llm+evaluation",
        "https://www.reddit.com/r/LocalLLaMA/.rss",
    ]

    def __init__(self):
        self.log("Scanner Agent is initializing")
        self.log("Scanner Agent is ready")

    def _from_feed(self) -> List[ScannedResource]:
        resources: List[ScannedResource] = []
        if feedparser is None:
            return resources
        for feed_url in self.FEEDS:
            try:
                parsed = feedparser.parse(feed_url)
                for entry in parsed.entries[:8]:
                    link = entry.get("link", "").strip()
                    title = entry.get("title", "").strip()
                    summary = entry.get("summary", "").strip()
                    if not link or not title:
                        continue
                    source = urlparse(link).netloc or "unknown"
                    resources.append(
                        ScannedResource(
                            title=title[:140],
                            url=link,
                            source=source,
                            snippet=summary[:320] or "No summary provided.",
                        )
                    )
            except Exception as exc:
                self.log(f"Feed failed for {feed_url}: {exc}")
        return resources

    def scan(self, topic: str, memory_urls: List[str]) -> ResourceSelection:
        self.log(f"Scanning sources for topic: {topic}")
        discovered = self._from_feed()
        if not discovered:
            self.log("Using fallback resources because no feed content was available")
            discovered = FALLBACK_RESOURCES[:]

        deduped = []
        seen = set(memory_urls)
        for resource in discovered:
            if resource.url in seen:
                continue
            # Lightweight relevance filter for the requested topic.
            text = f"{resource.title} {resource.snippet}".lower()
            if topic.lower() not in text and "llm" not in text and "agent" not in text:
                continue
            deduped.append(resource)

        selected = deduped[:10] if deduped else FALLBACK_RESOURCES[:3]
        self.log(f"Scanner Agent selected {len(selected)} candidate resources")
        return ResourceSelection(resources=selected)
