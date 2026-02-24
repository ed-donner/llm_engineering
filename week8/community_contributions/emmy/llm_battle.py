from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, Generator, List, Optional, Tuple

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------


@dataclass
class AgentConfig:
    """Holds configuration required to talk to an LLM provider."""

    name: str
    model: str
    api_key_env: str
    base_url_env: Optional[str] = None
    temperature: float = 0.7
    supports_json: bool = True


def load_client(config: AgentConfig) -> OpenAI:
    """Create an OpenAI-compatible client for the given agent."""
    api_key = os.getenv(config.api_key_env) or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            f"Missing API key for {config.name}. "
            f"Set {config.api_key_env} or OPENAI_API_KEY."
        )

    base_url = (
        os.getenv(config.base_url_env)
        if config.base_url_env
        else os.getenv("OPENAI_BASE_URL")
    )

    return OpenAI(api_key=api_key, base_url=base_url)


def extract_text(response) -> str:
    """Extract text content from an OpenAI-style response object or dict."""

    choices = getattr(response, "choices", None)
    if choices is None and isinstance(response, dict):
        choices = response.get("choices")
    if not choices:
        raise RuntimeError(f"LLM response missing choices field: {response!r}")

    choice = choices[0]
    message = getattr(choice, "message", None)
    if message is None and isinstance(choice, dict):
        message = choice.get("message")

    content = None
    if message is not None:
        content = getattr(message, "content", None)
        if content is None and isinstance(message, dict):
            content = message.get("content")

    if isinstance(content, list):
        parts: List[str] = []
        for part in content:
            if isinstance(part, dict):
                if "text" in part:
                    parts.append(str(part["text"]))
                elif "output_text" in part:
                    parts.append(str(part["output_text"]))
                elif "type" in part and "content" in part:
                    parts.append(str(part["content"]))
            else:
                parts.append(str(part))
        content = "".join(parts)

    if content is None:
        text = getattr(choice, "text", None)
        if text is None and isinstance(choice, dict):
            text = choice.get("text")
        if text:
            content = text

    if content is None:
        raise RuntimeError(f"LLM response missing content/text: {response!r}")

    return str(content).strip()


# Default configuration leverages OpenAI unless overrides are provided.
DEBATER_A_CONFIG = AgentConfig(
    name="Debater A",
    model=os.getenv("DEBATER_A_MODEL", "gpt-4o"),
    api_key_env="OPENAI_API_KEY",
    base_url_env="OPENAI_BASE_URL",
    temperature=float(os.getenv("DEBATER_A_TEMPERATURE", 0.7)),
)

DEBATER_B_CONFIG = AgentConfig(
    name="Debater B",
    model=os.getenv("DEBATER_B_MODEL", "gemini-2.0-flash"),
    api_key_env="GOOGLE_API_KEY",
    base_url_env="GEMINI_BASE_URL",
    temperature=float(os.getenv("DEBATER_B_TEMPERATURE", 0.7)),
)

JUDGE_CONFIG = AgentConfig(
    name="Judge",
    model=os.getenv("JUDGE_MODEL", "gpt-oss:20b-cloud"),
    api_key_env="OLLAMA_API_KEY",
    base_url_env="OLLAMA_BASE_URL",
    temperature=float(os.getenv("JUDGE_TEMPERATURE", 0.2)),
    supports_json=False,
)

REPORTER_CONFIG = AgentConfig(
    name="Reporter",
    model=os.getenv("REPORTER_MODEL", "MiniMax-M2"),
    api_key_env="MINIMAX_API_KEY",
    base_url_env="MINIMAX_BASE_URL",
    temperature=float(os.getenv("REPORTER_TEMPERATURE", 0.4)),
    supports_json=False,
)

THEME = gr.themes.Default(
    primary_hue="blue",
    secondary_hue="sky",
    neutral_hue="gray",
)

CUSTOM_CSS = """
body, .gradio-container {
    background: radial-gradient(circle at top, #0f172a 0%, #020617 60%, #020617 100%);
    color: #e2e8f0;
}
#live-debate-panel {
    background: linear-gradient(135deg, rgba(30,64,175,0.95), rgba(29,78,216,0.85));
    color: #f8fafc;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 20px 45px rgba(15,23,42,0.35);
}
#live-debate-panel h3 {
    color: #bfdbfe;
}
.gr-button-primary {
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    border: none !important;
}
.gr-button-primary:hover {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
}
"""

# ---------------------------------------------------------------------------
# Debate runtime classes
# ---------------------------------------------------------------------------


@dataclass
class DebateState:
    topic: str
    stance_a: str
    stance_b: str
    transcript: List[Tuple[str, str]] = field(default_factory=list)


class LLMAdapter:
    """Thin wrapper around the OpenAI SDK to simplify prompting."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = load_client(config)

    def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        max_tokens: int = 512,
        json_mode: bool = False,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        params = dict(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=max_tokens,
        )
        if json_mode and self.config.supports_json:
            params["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**params)
        return extract_text(response)


class Debater:
    def __init__(self, adapter: LLMAdapter, stance_label: str):
        self.adapter = adapter
        self.stance_label = stance_label

    def argue(self, topic: str) -> str:
        prompt = (
            f"You are {self.adapter.config.name}, debating the topic:\n"
            f"'{topic}'.\n\n"
            f"Present a concise argument that {self.stance_label.lower()} "
            f"the statement. Use at most 150 words. Provide clear reasoning "
            f"and, if applicable, cite plausible evidence or examples."
        )
        return self.adapter.complete(prompt, max_tokens=300)


class Judge:
    RUBRIC = [
        "Clarity of the argument",
        "Use of evidence or examples",
        "Logical coherence",
        "Persuasiveness and impact",
    ]

    def __init__(self, adapter: LLMAdapter):
        self.adapter = adapter

    def evaluate(self, topic: str, argument_a: str, argument_b: str) -> Dict[str, object]:
        rubric_text = "\n".join(f"- {item}" for item in self.RUBRIC)
        prompt = (
            "You are serving as an impartial debate judge.\n"
            f"Topic: {topic}\n\n"
            f"Argument from Debater A:\n{argument_a}\n\n"
            f"Argument from Debater B:\n{argument_b}\n\n"
            "Score each debater from 0-10 on the following criteria:\n"
            f"{rubric_text}\n\n"
            "Return a JSON object with this exact structure:\n"
            '{\n'
            '  "winner": "A" or "B" or "Tie",\n'
            '  "reason": "brief justification",\n'
            '  "scores": [\n'
            '    {"criterion": "...", "debater_a": 0-10, "debater_b": 0-10, "notes": "optional"}\n'
            "  ]\n"
            "}\n"
            "Ensure the JSON is valid."
        )
        raw = self.adapter.complete(prompt, max_tokens=400, json_mode=True)
        try:
            data = json.loads(raw)
            if "scores" not in data:
                raise ValueError("scores missing")
            return data
        except Exception:
            # Fallback: wrap raw text if parsing fails.
            return {"winner": "Unknown", "reason": raw, "scores": []}


class Reporter:
    def __init__(self, adapter: LLMAdapter):
        self.adapter = adapter

    def summarize(
        self,
        topic: str,
        argument_a: str,
        argument_b: str,
        judge_result: Dict[str, object],
    ) -> str:
        prompt = (
            f"Summarize a single-round debate on '{topic}'.\n\n"
            f"Debater A argued:\n{argument_a}\n\n"
            f"Debater B argued:\n{argument_b}\n\n"
            f"Judge verdict: {json.dumps(judge_result, ensure_ascii=False)}\n\n"
            "Provide a short journalistic summary (max 200 words) highlighting "
            "each side's key points and the judge's decision. Use neutral tone."
        )
        response = self.adapter.client.chat.completions.create(
            model=self.adapter.config.model,
            messages=[
                {"role": "system", "content": "You are an impartial debate reporter."},
                {"role": "user", "content": prompt},
            ],
            temperature=self.adapter.config.temperature,
            max_tokens=300,
            **(
                {"extra_body": {"reasoning_split": True}}
                if getattr(self.adapter.client, "base_url", None)
                and "minimax" in str(self.adapter.client.base_url).lower()
                else {}
            ),
        )
        return extract_text(response)


# ---------------------------------------------------------------------------
# Debate pipeline + UI
# ---------------------------------------------------------------------------


debater_a = Debater(LLMAdapter(DEBATER_A_CONFIG), stance_label="supports")
debater_b = Debater(LLMAdapter(DEBATER_B_CONFIG), stance_label="opposes")
judge = Judge(LLMAdapter(JUDGE_CONFIG))
reporter = Reporter(LLMAdapter(REPORTER_CONFIG))


def format_transcript(transcript: List[Tuple[str, str]]) -> str:
    """Return markdown-formatted transcript."""
    lines = []
    for speaker, message in transcript:
        lines.append(f"### {speaker}\n\n{message}\n")
    return "\n".join(lines)


def run_debate(
    topic: str, stance_a: str, stance_b: str
) -> Generator[Tuple[str, str, List[List[object]], str, str], None, None]:
    """Generator for Gradio to stream debate progress."""
    if not topic.strip():
        warning = "⚠️ Please enter a debate topic to get started."
        yield warning, "", [], "", ""
        return

    state = DebateState(topic=topic.strip(), stance_a=stance_a, stance_b=stance_b)

    state.transcript.append(
        ("Moderator", f"Welcome to the debate on **{state.topic}**!")
    )
    yield format_transcript(state.transcript), "Waiting for judge...", [], "", ""

    argument_a = debater_a.argue(state.topic)
    state.transcript.append((f"Debater A ({state.stance_a})", argument_a))
    yield format_transcript(state.transcript), "Collecting arguments...", [], "", ""

    argument_b = debater_b.argue(state.topic)
    state.transcript.append((f"Debater B ({state.stance_b})", argument_b))
    yield format_transcript(state.transcript), "Judge deliberating...", [], "", ""

    judge_result = judge.evaluate(state.topic, argument_a, argument_b)
    verdict_text = (
        f"Winner: {judge_result.get('winner', 'Unknown')}\nReason: "
        f"{judge_result.get('reason', 'No explanation provided.')}"
    )
    score_rows = [
        [
            entry.get("criterion", ""),
            entry.get("debater_a", ""),
            entry.get("debater_b", ""),
            entry.get("notes", ""),
        ]
        for entry in judge_result.get("scores", [])
    ]
    judge_report_md = (
        f"**Judge Verdict:** {judge_result.get('winner', 'Unknown')}\n\n"
        f"{judge_result.get('reason', '')}"
    )
    yield (
        format_transcript(state.transcript),
        judge_report_md,
        score_rows,
        verdict_text,
        format_transcript(state.transcript),
    )

    reporter_summary = reporter.summarize(
        state.topic, argument_a, argument_b, judge_result
    )

    final_markdown = (
        f"{judge_report_md}\n\n---\n\n"
        f"**Reporter Summary**\n\n{reporter_summary}"
    )
    yield (
        format_transcript(state.transcript),
        final_markdown,
        score_rows,
        verdict_text,
        format_transcript(state.transcript),
    )


# ---------------------------------------------------------------------------
# Gradio Interface
# ---------------------------------------------------------------------------


with gr.Blocks(
    title="LLM Debate Arena",
    fill_width=True,
    theme=THEME,
    css=CUSTOM_CSS,
) as demo:
    gr.Markdown(
        "# 🔁 LLM Debate Arena\n"
        "Configure two debating agents, watch their arguments in real time, and "
        "review the judge's verdict plus a reporter summary."
    )

    with gr.Row():
        topic_input = gr.Textbox(
            label="Debate Topic",
            placeholder="e.g., Should autonomous delivery robots be allowed in city centers?",
        )
    with gr.Row():
        stance_a_input = gr.Textbox(
            label="Debater A Stance",
            value="Supports the statement",
        )
        stance_b_input = gr.Textbox(
            label="Debater B Stance",
            value="Opposes the statement",
        )

    run_button = gr.Button("Start Debate", variant="primary")

    with gr.Tab("Live Debate"):
        transcript_md = gr.Markdown(
            "### Waiting for the debate to start...",
            elem_id="live-debate-panel",
        )

    with gr.Tab("Judge's Report"):
        judge_md = gr.Markdown("Judge verdict will appear here.")
        score_table = gr.Dataframe(
            headers=["Criterion", "Debater A", "Debater B", "Notes"],
            datatype=["str", "number", "number", "str"],
            interactive=False,
        )
        verdict_box = gr.Textbox(
            label="Verdict Detail",
            interactive=False,
        )
        transcript_box = gr.Textbox(
            label="Full Transcript (for copying)",
            interactive=False,
            lines=10,
        )

    run_button.click(
        fn=run_debate,
        inputs=[topic_input, stance_a_input, stance_b_input],
        outputs=[transcript_md, judge_md, score_table, verdict_box, transcript_box],
        queue=True,
    )

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=4).launch()
