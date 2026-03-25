"""
The solution uses finnhub to get the news articles and then uses Claude to analyse the articles.

Claude receives a news article and a system prompt that instructs it to
analyse the article by calling tools in a logical sequence. It decides
which tools to call, when, and with what arguments — running in an
agentic loop until it produces a final text response (the investment brief).

Agentic loop:
1. Claude calls get_sentiment(article)
2. Claude calls get_rag_context(article) — retrieves similar past articles
3. Claude actively reasons over RAG context (trend, contradiction, escalation, etc)
   then writes its analysis and calls cross_check(article, analysis)
4. Claude calls safeguard_check(article, analysis, contrarian)
5. Claude calls write_brief(...all inputs...)
6. Claude calls store_article(...) to persist for future RAG
7. Claude calls send_notification(...) for every article
8. Claude returns the final investment brief as text
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import openai

from config import APP_CONFIG
from tools import TOOL_DEFINITIONS, dispatch

logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = """You are an autonomous AI financial analyst. You will analyse a news article
by calling the available tools in this exact sequence:

1. Call get_sentiment(text)
   Classify the article's financial sentiment. Note the label and confidence score.

2. Call get_rag_context(text)
   Retrieve similar past articles from memory. Then ACTIVELY reason over them:
   - Is this a developing story? Has this topic appeared before?
   - How has sentiment shifted vs previous coverage? (e.g. getting more negative?)
   - Are there contradictions between this article and past articles?
   - Has the risk level escalated or de-escalated since last coverage?
   - Which entities keep appearing across multiple articles?
   You MUST reference these observations explicitly in your analysis in step 3.
   If no past articles exist yet, note this is a first-seen topic.

3. Write your analysis internally, then call cross_check(article, analysis).
   Your analysis argument must include ALL of the following:
   - Why this sentiment (with specific evidence from the article)
   - RAG comparison: how this article relates to past coverage on the same topic
     (sentiment trend, story escalation, contradictions, recurring entities)
   - Key entities involved (companies, regulators, people, markets)
   - Top 3 financial risks with brief reasoning for each
   If RAG returned no past articles, state clearly: "No prior coverage found."

4. Call safeguard_check(article, analysis, contrarian)
   Pass the full analysis and the contrarian view from step 3.
   This audits everything for hallucinations, alarmist language, manipulation.

5. Call write_brief(article, sentiment_label, sentiment_score, analysis,
                    contrarian, safeguard_verdict, safeguard_flags)
   Synthesise everything into a structured investment brief.
   The brief MUST include a "Prior Coverage" section that summarises what
   RAG context revealed — or states "First time seeing this story" if none.

6. Call store_article(text, sentiment_label, sentiment_score, safeguard_verdict)
   Persist this article so it becomes RAG context for future analyses.

7. Call send_notification(title, message, priority) for EVERY article:
   - priority=1 if safeguard verdict is FAIL or sentiment is negative
   - priority=0 if sentiment is positive or neutral
   - title format: "[SENTIMENT] [SCORE%] — [first 60 chars of headline]"
   - message: 2-sentence executive summary + recommendation + RAG trend note
     e.g. "Negative sentiment on Fed policy, 3rd consecutive bearish signal.
           Recommendation: AVOID rate-sensitive equities."

After all tool calls are complete, return ONLY the final investment brief text.
Do not add any preamble or explanation outside the brief itself."""


@dataclass
class AnalysisResult:
    """Holds the complete output of one article's analysis pipeline."""
    article_text:      str        = ""
    headline:          str        = ""
    source:            str        = ""
    published_at:      str        = ""
    sentiment_label:   str        = ""
    sentiment_score:   float      = 0.0
    rag_articles:      list[dict] = field(default_factory=list)
    rag_summary:       str        = ""   
    analyst_notes:     str        = ""
    contrarian_view:   str        = ""
    safeguard_verdict: str        = ""
    safeguard_flags:   list[str]  = field(default_factory=list)
    investment_brief:  str        = ""
    notification_sent: bool       = False
    tool_calls_made:   list[str]  = field(default_factory=list)
    error:             str        = ""


class Orchestrator:
    """
    Drives the agentic loop.
    """

    MAX_ITERATIONS = 20   # safety cap

    def __init__(self) -> None:
        self._client = openai.OpenAI(
            api_key=APP_CONFIG.openrouter_api_key,
            base_url=APP_CONFIG.models.openrouter_base_url,
            default_headers={"X-Title": "AI Financial News Analyst"},
        )

    def analyse(self, article: dict[str, Any]) -> AnalysisResult:
        """
        Parameters
        ----------
        article : dict
            Keys: headline, summary, source, published_at, related, url, _id

        Returns
        -------
        AnalysisResult
        """
        headline  = article.get("headline", "")
        summary   = article.get("summary", "")
        related   = article.get("related", "")
        source    = article.get("source", "unknown")
        published = article.get("published_at", "")

        full_text = "\n".join(filter(None, [
            headline,
            summary,
            f"Tickers: {related}" if related else "",
        ]))

        result = AnalysisResult(
            article_text = full_text,
            headline     = headline,
            source       = source,
            published_at = published,
        )

        
        messages: list[dict] = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Please analyse this financial news article:\n\n"
                    f"**Headline:** {headline}\n"
                    f"**Source:** {source}  |  **Published:** {published}\n"
                    f"**Summary:** {summary}\n"
                    + (f"**Related tickers:** {related}" if related else "")
                ),
            },
        ]

        #agentic loop 
        for iteration in range(self.MAX_ITERATIONS):
            response = self._client.chat.completions.create(
                model=APP_CONFIG.models.claude_model,
                max_tokens=APP_CONFIG.models.claude_max_tokens,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                messages=messages,
            )

            msg    = response.choices[0].message
            finish = response.choices[0].finish_reason

            #append assistant turn to conversation
            messages.append(msg.model_dump(exclude_unset=False))

            #no more tool calls
            if finish == "stop" or not msg.tool_calls:
                result.investment_brief = (msg.content or "").strip()
                logger.info(
                    "Agentic loop complete after %d iterations. "
                    "Tools called: %s",
                    iteration + 1,
                    " → ".join(result.tool_calls_made),
                )
                break

            #process each tool call requested
            tool_results: list[dict] = []
            for tc in msg.tool_calls:
                tool_name = tc.function.name
                try:
                    tool_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                logger.info(
                    "[Loop:%d] Claude calls %s(%s)",
                    iteration,
                    tool_name,
                    str(tool_args)[:120],
                )

                result.tool_calls_made.append(tool_name)

                #execute
                tool_output_str = dispatch(tool_name, tool_args)
                tool_output     = json.loads(tool_output_str)

                #mirror key results back into AnalysisResult for the UI
                self._mirror_to_result(result, tool_name, tool_output, tool_args)

                tool_results.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "content":      tool_output_str,
                })

            #append all tool results in one turn
            messages.extend(tool_results)

        else:
            result.error = (
                f"Reached MAX_ITERATIONS ({self.MAX_ITERATIONS}) without finishing."
            )
            logger.warning(result.error)

        return result

    #helpers

    @staticmethod
    def _mirror_to_result(
        result: AnalysisResult,
        tool_name: str,
        output: dict,
        args: dict,
    ) -> None:
        """Copy tool outputs into AnalysisResult so the Gradio UI can read them."""

        if tool_name == "get_sentiment":
            result.sentiment_label = output.get("label", "")
            result.sentiment_score = output.get("score", 0.0)

        elif tool_name == "get_rag_context":
            result.rag_articles = output.get("articles", [])
            count = output.get("count", 0)
            if count == 0:
                result.rag_summary = "No prior coverage found — first time seeing this topic."
            else:
                #build a human-readable summary of what was retrieved
                snippets = "; ".join(
                    f"[{a['metadata'].get('ingested_at', 'n/a')[:10]}] "
                    f"{a['metadata'].get('sentiment','?')} "
                    f"(dist={a['distance']:.2f}): "
                    f"{a['text'][:80]}…"
                    for a in result.rag_articles
                )
                result.rag_summary = (
                    f"{count} similar past article(s) retrieved:\n{snippets}"
                )
                logger.info(
                    "[RAG] %d past articles retrieved for context.", count
                )

        elif tool_name == "cross_check":
            result.contrarian_view = output.get("contrarian_view", "")
            # Capture the analysis Claude passed as an argument
            result.analyst_notes   = args.get("analysis", "")

        elif tool_name == "safeguard_check":
            result.safeguard_verdict = output.get("verdict", "")
            result.safeguard_flags   = output.get("flags", [])

        elif tool_name == "write_brief":
            result.investment_brief = output.get("brief", "")

        elif tool_name == "send_notification":
            result.notification_sent = output.get("sent", False)