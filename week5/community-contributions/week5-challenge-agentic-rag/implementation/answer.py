import os
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable
    
from chromadb import PersistentClient
from dotenv import load_dotenv
from litellm import _turn_on_debug, completion
from openai import OpenAI
from pydantic import BaseModel, Field
from tenacity import retry, wait_exponential

from evaluation.utils import AnswerEval, score_answer


load_dotenv(override=True)

if os.getenv("LITELLM_DEBUG", "0").lower() in {"1", "true", "yes"}:
    _turn_on_debug()

# Toggle agent debug logging with DEBUG_RAG_AGENT (integer levels)
try:
    DEBUG_RAG_AGENT = int(os.getenv("DEBUG_RAG_AGENT", "0"))
except ValueError:
    DEBUG_RAG_AGENT = 0

MODEL = "groq/openai/gpt-oss-120b"
JUDGE_MODEL = os.getenv("AGENT_JUDGE_MODEL", "gpt-4.1-nano")

DB_NAME = str(Path(__file__).parent.parent / "preprocessed_db")
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent.parent.parent / "knowledge-base"

collection_name = "docs"
embedding_model = "text-embedding-3-large"
wait = wait_exponential(multiplier=1, min=10, max=240)

openai = OpenAI()

chroma = PersistentClient(path=DB_NAME)
collection = chroma.get_or_create_collection(collection_name)

RETRIEVAL_K = 20
FINAL_K = 10
CHUNK_SNIPPET_LENGTH = 350
MAX_AGENT_TURNS = 15
MAX_ERROR_RETRIES = 8

# Score thresholds for final_answer
ACCURACY_THRESHOLD = 5
RELEVANCE_THRESHOLD = 5
COMPLETENESS_THRESHOLD = 4

ALLOWED_ACTIONS = {
    "vector_search",
    "text_search",
    "rerank",
    "judge_answer",
    "final_answer",
}


class Result(BaseModel):
    page_content: str
    metadata: dict[str, Any]


@dataclass
class ToolSpec:
    """Description of an available tool surfaced to the controller LLM."""

    name: str
    description: str
    usage: str


@dataclass
class ParsedAction:
    """Parsed ReAct step emitted by the controller."""

    action: str
    query: str | None = None
    answer: str | None = None
    mode: str | None = None
    raw_action_input: str | None = None
    thought: str | None = None
    final_answer: str | None = None


class AgentController:
    """Lightweight controller that asks an LLM which tool to call next."""

    def __init__(self, model: str, tools: Iterable[ToolSpec], max_turns: int = 6):
        self.model = model
        self.tools = list(tools)
        self.max_turns = max_turns

    def choose_action(
        self,
        *,
        question: str,
        history: str,
        current_context: str,
        agent_turn: str,
        reasoning_history: str,
    ) -> str:
        """Ask the controller LLM which action to take next using a ReAct prompt."""
        tool_descriptions = "\n".join(
            f"- {tool.name}: {tool.description}\nUsage: {tool.usage}" for tool in self.tools
        )

        system_prompt = f"""
You are a ReAct-style retrieval agent for Insurellm.

## OUTPUT FORMAT (REQUIRED)

Each response MUST follow this format, with each element on its own line:

Thought: <your reasoning>
Action: <vector_search | text_search | rerank | judge_answer | final_answer>
Action Input: <JSON or string, or "" for tools with no parameters>

## WORKFLOW

1. Start with vector_search using the original question
2. Call rerank to order chunks by relevance
3. Call judge_answer with your draft answer to get scores
4. If scores meet thresholds (Accuracy={ACCURACY_THRESHOLD}, Relevance={RELEVANCE_THRESHOLD}, Completeness≥{COMPLETENESS_THRESHOLD}), call final_answer
5. Otherwise, retrieve more context and repeat from step 2

## RULES

- Ground answers ONLY in retrieved context. Never invent facts.
- Never repeat the same search query. Check Reasoning History.
- text_search requires ONE WORD ONLY (e.g., "Thompson" not "Maxine Thompson")
- Always call rerank before judge_answer
- Always call judge_answer before final_answer

## AFTER JUDGE_ANSWER

Your next Thought MUST:
- Restate the three scores from the Observation
- Identify which dimension(s) need improvement
- Decide whether vector_search or text_search would better address the gap

Available tools:
{tool_descriptions}
"""

        user_prompt = f"""
# User Question
{question}

# Conversation History
{history or 'None'}

# Current Retrieved Context
{current_context or 'None'}

# Reasoning History
{reasoning_history or 'None'}

# Current Agent Turn
{agent_turn}

Continue the ReAct loop. Produce either:
- Thought + Action + Action Input
- OR Thought + Final Answer
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        if DEBUG_RAG_AGENT >= 3:
            print("======================= User prompt:")
            print(user_prompt)
            print("=======================")

        response = completion(
            model=self.model,
            messages=messages,
            timeout=60,  # 60 second timeout to prevent hanging
        )
        if DEBUG_RAG_AGENT >= 4:
            try:
                import json as _json  # local import to avoid shadowing
                print("[DEBUG_RAG_AGENT] Full LLM response:")
                print(_json.dumps(response.model_dump(), indent=2))
            except Exception:
                print("[DEBUG_RAG_AGENT] (Unable to pretty-print LLM response)")
        choice = response.choices[0].message
        content = getattr(choice, "content", None) or ""
        reasoning = getattr(choice, "reasoning", None) or ""

        # Some models (e.g., openai/gpt-oss-120b) put ReAct output in reasoning field
        # Prefer reasoning if it contains ReAct format and content doesn't
        if reasoning and ("Thought:" in reasoning or "Action:" in reasoning):
            if not ("Thought:" in content or "Action:" in content):
                content = reasoning

        return content


@dataclass
class RetrievalBatch:
    modality: str  # e.g., "vector" or "text"
    query: str
    results: list[Result]


class RankOrder(BaseModel):
    order: list[int] = Field(
        description="The order of relevance of chunks, from most relevant to least relevant, by chunk id number"
    )


class AgentState:
    """Shared mutable state for the agent loop."""

    def __init__(
        self,
        question: str,
        history: list[dict[str, str]] | None = None,
    ):
        self.question = question
        self.history = history or []
        self.chunk_ids: dict[str, int] = {}
        self.next_chunk_id = 1
        self.current_chunks: list[Result] = []
        self.retrieval_batches: list[RetrievalBatch] = []
        self.final_answer: str | None = None
        self.eval_feedback: AnswerEval | None = None
        self.react_history: str = ""
        self.agent_done: bool = False
        self.explicitly_reranked: bool = False

    def register_chunk(self, chunk: Result) -> int:
        if chunk.page_content in self.chunk_ids:
            return self.chunk_ids[chunk.page_content]
        chunk_id = self.next_chunk_id
        self.next_chunk_id += 1
        self.chunk_ids[chunk.page_content] = chunk_id
        return chunk_id

    def add_retrieval_batch(self, batch: RetrievalBatch) -> None:
        for chunk in batch.results:
            self.register_chunk(chunk)
        self.retrieval_batches.append(batch)

    def merged_chunks(self) -> list[Result]:
        merged: list[Result] = []
        seen = set()
        for batch in self.retrieval_batches:
            for chunk in batch.results:
                if chunk.page_content in seen:
                    continue
                seen.add(chunk.page_content)
                merged.append(chunk)
        return merged

    def context_chunks(self) -> list[Result]:
        return self.current_chunks[:FINAL_K]

    def log(
        self,
        tool: str,
        tool_input: str,
        observation: str,
        *,
        reason: str | None = None,
    ) -> None:
        """Log tool execution for debugging purposes."""
        if DEBUG_RAG_AGENT >= 2:
            trimmed_obs = observation.strip()
            if len(trimmed_obs) > 1200:
                trimmed_obs = trimmed_obs[:1200] + "..."
            print(f"[DEBUG_RAG_AGENT] Observation:")
            print(f"  {trimmed_obs}")


@retry(wait=wait)
def rerank(question: str, chunks: list[Result]) -> list[Result]:
    system_prompt = """
You are a document re-ranker.
You are provided with a question and a list of relevant chunks of text from a query of a knowledge base.
The chunks are provided in the order they were retrieved; this should be approximately ordered by relevance, but you may be able to improve on that.
You must rank order the provided chunks by relevance to the question, with the most relevant chunk first.
Reply only with the list of ranked chunk ids, nothing else. Include all the chunk ids you are provided with, reranked.
"""
    user_prompt = f"The user has asked the following question:\n\n{question}\n\nOrder all the chunks of text by relevance to the question, from most relevant to least relevant. Include all the chunk ids you are provided with, reranked.\n\n"
    user_prompt += "Here are the chunks:\n\n"
    for index, chunk in enumerate(chunks):
        user_prompt += f"# CHUNK ID: {index + 1}:\n\n{chunk.page_content}\n\n"
    user_prompt += "Reply only with the list of ranked chunk ids, nothing else."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = completion(model=MODEL, messages=messages, response_format=RankOrder)
    reply = response.choices[0].message.content
    order = RankOrder.model_validate_json(reply).order
    return [chunks[i - 1] for i in order]


def search_knowledge_base(
    query: str,
    *,
    max_results: int = 5,
    mode: str = "auto",
) -> list[Result]:
    """Perform a keyword search across markdown files, matching any term and ranking by coverage."""
    tokens = [term for term in query.lower().split() if term]
    if not tokens:
        return []

    def best_matches(require_all: bool) -> list[Result]:
        per_file_best: dict[str, tuple[int, int, Result]] = {}
        for md_file in KNOWLEDGE_BASE_PATH.rglob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
            except OSError:
                continue
            for para in text.split("\n\n"):
                snippet = para.strip()
                if not snippet:
                    continue
                lower_para = snippet.lower()
                hits = [t for t in tokens if t in lower_para]
                if require_all and len(hits) != len(tokens):
                    continue
                if not require_all and not hits:
                    continue
                score = len(hits)
                # prefer shorter paragraphs on ties
                key = md_file.as_posix()
                existing = per_file_best.get(key)
                if existing is None or score > existing[0] or (
                    score == existing[0] and len(snippet) < existing[1]
                ):
                    per_file_best[key] = (
                        score,
                        len(snippet),
                        Result(
                            page_content=snippet,
                            metadata={
                                "source": key,
                                "type": "text_search",
                                "keywords": hits,
                            },
                        ),
                    )
        ranked = sorted(per_file_best.values(), key=lambda x: (-x[0], x[1]))
        return [item[2] for item in ranked[:max_results]]

    mode_normalized = (mode or "auto").lower()
    if mode_normalized == "and":
        return best_matches(require_all=True)
    if mode_normalized == "or":
        return best_matches(require_all=False)
    # Auto: try strict AND first; if nothing, fall back to OR.
    results = best_matches(require_all=True)
    if results:
        return results
    return best_matches(require_all=False)


def format_judge_evaluation(evaluation: AnswerEval) -> str:
    """Return a brief textual summary of the latest judge scores."""
    return (
        f"Feedback: {evaluation.feedback}\n"
        f"Scores -> Accuracy: {evaluation.accuracy}, "
        f"Completeness: {evaluation.completeness}, "
        f"Relevance: {evaluation.relevance}"
    )


def format_history(history: list[dict[str, str]]) -> str:
    if not history:
        return ""
    lines = []
    for turn in history[-6:]:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        lines.append(f"{role.title()}: {content}")
    return "\n".join(lines)


def format_context_chunks(chunks: list[Result]) -> str:
    """Format full chunk content for the current context section."""
    if not chunks:
        return "No chunks retrieved yet."
    lines = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.metadata.get("source", "unknown")
        lines.append(f"--- Chunk {i} (Source: {source}) ---")
        lines.append(chunk.page_content)
        lines.append("")
    return "\n".join(lines)


def append_react_block(
    state: AgentState,
    *,
    thought: str | None = None,
    action: str | None = None,
    action_input: str | None = None,
    observation: str | None = None,
    final_answer: str | None = None,
) -> None:
    """Append a formatted ReAct block to state.react_history."""
    lines: list[str] = []
    lines.append(f"Thought: {thought or 'None'}")
    if final_answer is not None:
        lines.append(f"Final Answer: {final_answer}")
    else:
        lines.append(f"Action: {action or 'None'}")
        lines.append(f"Action Input: {action_input or 'None'}")
        lines.append(f"Observation: {observation or 'None'}")
    block = "\n".join(lines)
    state.react_history = "\n\n".join([text for text in [state.react_history, block] if text]).strip()


def strip_code_fences(text: str) -> str:
    """Remove simple markdown code fences to help JSON parsing."""
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        stripped = stripped[3:-3].strip()
    if stripped.lower().startswith("json"):
        stripped = stripped[4:].strip()
    return stripped


def parse_react_output(text: str) -> ParsedAction:
    """Parse Thought / Action / Action Input / Final Answer blocks.

    Handles both well-formed (newline-separated) and malformed (run-together) output.
    """
    import re
    tool_names = ["vector_search", "text_search", "rerank", "judge_answer", "final_answer"]

    # First, try to normalize run-together format by inserting newlines before markers
    # This handles cases like "...contract.Thought: I will..." or "...answer.Action: judge_answer"
    normalized = re.sub(r'(?i)(?<=[.!?\"\'])\s*(Thought:|Action:|Action Input:|Final Answer:)', r'\n\1', text)

    thought_lines: list[str] = []
    action: str | None = None
    action_input_lines: list[str] = []
    final_answer_lines: list[str] = []
    current: str | None = None
    for raw_line in normalized.splitlines():
        line = raw_line.strip()
        lower = line.lower()
        if lower.startswith("thought:"):
            current = "thought"
            thought_lines.append(line.split(":", 1)[1].strip())
            continue
        if lower.startswith("action input:"):
            current = "action_input"
            action_input_lines.append(line.split(":", 1)[1].strip())
            continue
        if lower.startswith("action:"):
            current = "action"
            action = line.split(":", 1)[1].strip()
            continue
        if lower.startswith("final answer:"):
            current = "final"
            final_answer_lines.append(line.split(":", 1)[1].strip())
            continue
        if current == "thought":
            thought_lines.append(line)
        elif current == "action_input":
            action_input_lines.append(line)
        elif current == "final":
            final_answer_lines.append(line)
    # Fallback: infer action from free-form text if not explicitly labeled.
    if not action:
        lowered = text.lower()
        for name in tool_names:
            if name in lowered:
                action = name
                break
    raw_action_input = "\n".join(action_input_lines).strip() or None
    # Fallback: grab first JSON-like block if no explicit Action Input was found.
    if raw_action_input is None:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            raw_action_input = text[start : end + 1].strip()
    parsed = ParsedAction(
        action=(action or "").strip(),
        raw_action_input=raw_action_input,
        thought=("\n".join(thought_lines).strip() or None),
        final_answer=("\n".join(final_answer_lines).strip() or None),
    )
    if parsed.action and parsed.action not in ALLOWED_ACTIONS and parsed.final_answer is None:
        parsed.action = "error"
    if not parsed.action and not parsed.final_answer:
        parsed.action = "error"
    return parsed


def populate_action_fields(parsed: ParsedAction) -> ParsedAction:
    """Fill query/answer/mode fields from the raw action input."""
    raw_input = strip_code_fences(parsed.raw_action_input or "")
    parsed.raw_action_input = raw_input or parsed.raw_action_input
    input_obj: Any = raw_input
    if raw_input:
        try:
            input_obj = json.loads(raw_input)
        except json.JSONDecodeError:
            input_obj = raw_input
    else:
        input_obj = ""

    query = None
    answer = None
    mode = None
    if isinstance(input_obj, dict):
        query = input_obj.get("query") or input_obj.get("question") or input_obj.get("q")
        answer = input_obj.get("answer") or input_obj.get("final_answer")
        mode = input_obj.get("mode") or input_obj.get("search_mode")
        input_field = input_obj.get("input")
        if isinstance(input_field, str):
            if parsed.action in {"vector_search", "text_search"} and not query:
                query = input_field
            if parsed.action in {"judge_answer", "final_answer"} and not answer:
                answer = input_field
    else:
        input_str = str(input_obj).strip()
        if parsed.action in {"vector_search", "text_search"}:
            query = input_str or None
        elif parsed.action in {"judge_answer", "final_answer"}:
            answer = input_str or None
        else:
            query = input_str or None

    parsed.query = query
    parsed.answer = answer
    parsed.mode = mode
    if parsed.action and parsed.action not in ALLOWED_ACTIONS and parsed.final_answer is None:
        parsed.action = "error"
    if not parsed.action and not parsed.final_answer:
        parsed.action = "error"
    return parsed

def call_vector_search(state: AgentState, action: ParsedAction) -> str:
    if not action.query:
        return "Vector search requires a 'query' field, but none was provided."
    query = action.query.strip()
    embedding = openai.embeddings.create(model=embedding_model, input=[query]).data[0].embedding
    results = collection.query(query_embeddings=[embedding], n_results=RETRIEVAL_K)
    chunks: list[Result] = []
    for result in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append(Result(page_content=result[0], metadata=result[1]))
    batch = RetrievalBatch(modality="vector", query=query, results=chunks)
    state.add_retrieval_batch(batch)
    # Append new chunks to current_chunks (deduplicated)
    seen = {c.page_content for c in state.current_chunks}
    for chunk in chunks:
        if chunk.page_content not in seen:
            state.current_chunks.append(chunk)
            seen.add(chunk.page_content)
    # Show results from THIS search, not global list
    summaries = []
    top_ids = []
    for chunk in chunks[:FINAL_K]:
        chunk_id = state.register_chunk(chunk)
        top_ids.append(chunk_id)
        snippet = chunk.page_content.replace("\n", " ")
        snippet = (
            snippet[:CHUNK_SNIPPET_LENGTH] + "..."
            if len(snippet) > CHUNK_SNIPPET_LENGTH
            else snippet
        )
        summaries.append(
            f"[{chunk_id}] {snippet}"
        )
    observation = (
        f"Retrieved {len(chunks)} chunks: {top_ids}\nSummary: " + (" | ".join(summaries) if summaries else "No results were returned.")
    )
    return observation


def call_rerank(state: AgentState, action: ParsedAction) -> str:
    if not state.current_chunks:
        observation = "No chunks available to rerank yet. Run searches first."
        return observation
    ranked = rerank(state.question, state.current_chunks)
    top_chunks = ranked[:FINAL_K]
    state.current_chunks = top_chunks
    state.explicitly_reranked = True
    ordered_ids = [state.chunk_ids.get(chunk.page_content, -1) for chunk in top_chunks]
    observation = f"Current chunk set reranked. Top chunk IDs: {ordered_ids}"
    return observation


def call_text_search(state: AgentState, action: ParsedAction) -> str:
    if not action.query:
        return "Text search requires a 'query' field."
    query = action.query.strip()
    matches = search_knowledge_base(query, mode=action.mode or "auto")
    if not matches:
        observation = f"No text matches found for '{query}'."
        return observation
    batch = RetrievalBatch(modality="text", query=query, results=matches)
    state.add_retrieval_batch(batch)
    # Append new chunks to current_chunks (deduplicated)
    seen = {c.page_content for c in state.current_chunks}
    for match in matches:
        if match.page_content not in seen:
            state.current_chunks.append(match)
            seen.add(match.page_content)
    # Show results from THIS search, not global list
    summaries = []
    top_ids: list[int] = []
    for match in matches[:FINAL_K]:
        chunk_id = state.register_chunk(match)
        top_ids.append(chunk_id)
        snippet = match.page_content.replace("\n", " ")
        snippet = snippet[:CHUNK_SNIPPET_LENGTH] + ("..." if len(snippet) > CHUNK_SNIPPET_LENGTH else "")
        keywords = match.metadata.get("keywords", [])
        if keywords:
            keyword_str = ", ".join(keywords)
            summaries.append(f"[{chunk_id}] Keywords: {keyword_str} | {snippet}")
        else:
            summaries.append(f"[{chunk_id}] {snippet}")
    observation = f"Retrieved {len(matches)} chunks: {top_ids}\nSummary: " + (" | ".join(summaries) if summaries else "No results were returned.")
    return observation


def call_judge_answer(state: AgentState, action: ParsedAction) -> str:
    if not action.answer:
        return "judge_answer requires an explicit 'answer' in Action Input."

    # Safety net: auto-rerank if chunks exist but haven't been explicitly reranked
    if state.current_chunks and not state.explicitly_reranked:
        ranked = rerank(state.question, state.current_chunks)
        state.current_chunks = ranked[:FINAL_K]

    answer_to_score = action.answer.strip()
    state.final_answer = answer_to_score
    reference = "\n\n".join(chunk.page_content for chunk in state.context_chunks()) or ""
    evaluation = score_answer(
        state.question,
        answer_to_score,
        reference or "No supporting context was found.",
        model=JUDGE_MODEL,
    )
    state.eval_feedback = evaluation
    return format_judge_evaluation(evaluation)


def call_final_answer(state: AgentState, action: ParsedAction) -> str:
    if not action.answer:
        return "final_answer requires an explicit 'answer' in Action Input. Provide the answer text via the 'answer' field."

    # Validate: judge_answer must have been called at least once
    if not state.eval_feedback:
        return (
            f"Cannot call final_answer yet - you have not called judge_answer to evaluate your draft answer. "
            f"Follow the workflow: retrieve context, call rerank, draft an answer, then call judge_answer with your draft. "
            f"Once judge_answer returns scores that meet the thresholds (Accuracy={ACCURACY_THRESHOLD}, Relevance={RELEVANCE_THRESHOLD}, Completeness≥{COMPLETENESS_THRESHOLD}), you can call final_answer."
        )

    # Validate: scores must meet thresholds
    if not (
        state.eval_feedback.accuracy >= ACCURACY_THRESHOLD
        and state.eval_feedback.relevance >= RELEVANCE_THRESHOLD
        and state.eval_feedback.completeness >= COMPLETENESS_THRESHOLD
    ):
        current_scores = f"Accuracy={state.eval_feedback.accuracy:.1f}, Relevance={state.eval_feedback.relevance:.1f}, Completeness={state.eval_feedback.completeness:.1f}"
        return (
            f"Cannot call final_answer yet - your scores do not meet the required thresholds. "
            f"Current scores: {current_scores}. Required: Accuracy={ACCURACY_THRESHOLD}, Relevance={RELEVANCE_THRESHOLD}, Completeness≥{COMPLETENESS_THRESHOLD}. "
            f"You need to retrieve more context and refine your answer. Call rerank, then judge_answer with an improved draft."
        )

    state.final_answer = action.answer.strip()
    state.agent_done = True
    if DEBUG_RAG_AGENT >= 2:
        final_preview = state.final_answer[:200] + "..." if len(state.final_answer) > 200 else state.final_answer
        print(f"[DEBUG_RAG_AGENT] Final answer set: {final_preview}")
    return f"Final answer recorded. Scores: Accuracy={state.eval_feedback.accuracy:.1f}, Relevance={state.eval_feedback.relevance:.1f}, Completeness={state.eval_feedback.completeness:.1f}"


TOOL_HANDLERS = {
    "vector_search": call_vector_search,
    "text_search": call_text_search,
    "rerank": call_rerank,
    "judge_answer": call_judge_answer,
    "final_answer": call_final_answer,
}


def build_controller() -> AgentController:
    tools = [
        ToolSpec(
            name="vector_search",
            description="Runs a vector retrieval against the Chroma knowledge base using the provided query and adds results to the current chunk set.",
            usage="Provide the search query in the 'query' field.",
        ),
        ToolSpec(
            name="text_search",
            description="Performs a keyword search across the markdown knowledge base; returns the best matching paragraph per file and adds results to the current chunk set.",
            usage="Query must be ONE WORD ONLY (e.g., 'Thompson', 'IIOTY', 'Carllm'). Never use multiple words or phrases. For names, use ONLY the last name.",
        ),
        ToolSpec(
            name="rerank",
            description="Reranks all accumulated chunks by relevance to the question and updates the top-k ordering. You MUST call this before EVERY judge_answer call.",
            usage="No parameters required. Use empty string \"\" for Action Input.",
        ),
        ToolSpec(
            name="judge_answer",
            description="Evaluates a draft answer and returns Accuracy, Completeness, and Relevance scores (1-5 each). ALWAYS call rerank immediately before calling this to ensure chunks are properly ordered. Use this to check if your answer meets the required thresholds (5/5/4) before calling final_answer.",
            usage="Supply the draft answer text via the 'answer' field. Required. The Observation will contain the three scores.",
        ),
        ToolSpec(
            name="final_answer",
            description="Saves the provided answer as the final response. Only call this AFTER judge_answer returns scores that meet all thresholds (Accuracy=5, Relevance=5, Completeness≥4).",
            usage="Provide the answer text via the 'answer' field. Required. This must be the same answer that achieved passing scores from judge_answer.",
        ),
    ]
    return AgentController(model=MODEL, tools=tools, max_turns=MAX_AGENT_TURNS)


def run_agent(
    question: str,
    history: list[dict[str, str]] | None = None,
) -> tuple[str, list[Result]]:
    state = AgentState(question, history)
    controller = build_controller()
    history_text = format_history(state.history)
    error_retries = 0

    turn = 1
    if DEBUG_RAG_AGENT >= 2:
        print("\n\n")
        print("=" * 80)
        print(f"[DEBUG_RAG_AGENT] User question: {question}")
        print("=" * 80)
    while turn <= MAX_AGENT_TURNS:
        if DEBUG_RAG_AGENT >= 2:
            print("\n")
            print("-" * 80)
            print(f"[DEBUG_RAG_AGENT] Agent turn {turn}/{MAX_AGENT_TURNS}")
            print(f"[DEBUG_RAG_AGENT] Requesting next action from LLM...")
        try:
            raw_response = controller.choose_action(
                question=question,
                history=history_text,
                current_context=format_context_chunks(state.context_chunks()),
                agent_turn=f"{turn} of {MAX_AGENT_TURNS}",
                reasoning_history=state.react_history,
            )
        except Exception as exc:
            if DEBUG_RAG_AGENT >= 2:
                print(
                    f"[DEBUG_RAG_AGENT] LLM error ({exc.__class__.__name__}):"
                    f" {exc}. Retrying turn..."
                )
            error_retries += 1
            if error_retries >= MAX_ERROR_RETRIES:
                if DEBUG_RAG_AGENT >= 2:
                    print(
                        f"[DEBUG_RAG_AGENT] Aborting after {error_retries} agent errors."
                    )
                break
            continue

        parsed_action = populate_action_fields(parse_react_output(raw_response))
        parsed_action.action = parsed_action.action.lower().strip()

        # Convert "Final Answer:" format to final_answer tool call
        if parsed_action.final_answer and not parsed_action.action:
            parsed_action.action = "final_answer"
            parsed_action.answer = parsed_action.final_answer

        if parsed_action.action == "error":
            correction = (
                "Your last response did not follow the required ReAct format. "
                "Please respond with:\nThought: <reasoning>\nAction: <tool>\nAction Input: <json or string>"
            )
            if DEBUG_RAG_AGENT >= 2:
                print(f"[DEBUG_RAG_AGENT] Parse error: LLM response did not follow ReAct format.")
                print(f"  Sending correction and retrying (error_retries: {error_retries + 1})")
            append_react_block(
                state,
                thought=parsed_action.thought,
                action="error",
                action_input=parsed_action.raw_action_input,
                observation=correction,
            )
            error_retries += 1
            if error_retries >= MAX_ERROR_RETRIES:
                if DEBUG_RAG_AGENT >= 2:
                    print(
                        f"[DEBUG_RAG_AGENT] Aborting after {error_retries} agent errors."
                    )
                break
            turn += 1
            continue

        if DEBUG_RAG_AGENT >= 2:
            print("[DEBUG_RAG_AGENT] Agent selected action:")
            print(f"  Thought:    {parsed_action.thought or 'N/A'}")
            print(f"  Action:       {parsed_action.action or 'None'}")
            print(f"  Action Input: {parsed_action.raw_action_input or parsed_action.query or 'None'}")

        handler = TOOL_HANDLERS.get(parsed_action.action)
        if not handler:
            observation = f"Unknown action '{parsed_action.action}'. Available actions: vector_search, text_search, rerank, judge_answer, final_answer."
            append_react_block(
                state,
                thought=parsed_action.thought,
                action=parsed_action.action,
                action_input=parsed_action.raw_action_input,
                observation=observation,
            )
            if DEBUG_RAG_AGENT >= 2:
                print(f"[DEBUG_RAG_AGENT] Observation:")
                print(f"  {observation}")
            error_retries += 1
            if error_retries >= MAX_ERROR_RETRIES:
                if DEBUG_RAG_AGENT >= 2:
                    print(
                        f"[DEBUG_RAG_AGENT] Aborting after {error_retries} agent errors."
                    )
                break
            turn += 1
            continue

        if DEBUG_RAG_AGENT >= 2:
            print(f"[DEBUG_RAG_AGENT] Executing action: {parsed_action.action}")
        try:
            observation = handler(state, parsed_action)
            state.log(
                parsed_action.action,
                parsed_action.raw_action_input
                or parsed_action.query
                or parsed_action.answer
                or "",
                observation if isinstance(observation, str) else "Call completed.",
                reason=parsed_action.thought,
            )
        except Exception as exc:
            if DEBUG_RAG_AGENT >= 2:
                print(
                    f"[DEBUG_RAG_AGENT] Tool call error ({exc.__class__.__name__}):"
                    f" {exc}. Retrying turn..."
                )
            error_retries += 1
            if error_retries >= MAX_ERROR_RETRIES:
                if DEBUG_RAG_AGENT >= 2:
                    print(
                        f"[DEBUG_RAG_AGENT] Aborting after {error_retries} agent errors."
                    )
                break
            turn += 1
            continue
        error_retries = 0

        observation_text = observation if isinstance(observation, str) else "Call completed."
        append_react_block(
            state,
            thought=parsed_action.thought,
            action=parsed_action.action,
            action_input=parsed_action.raw_action_input,
            observation=observation_text,
        )

        turn += 1
        if state.agent_done:
            break

    # Dump reasoning history on exit
    if DEBUG_RAG_AGENT >= 1:
        print("\n\n")
        print("=" * 80)
        print("[DEBUG_RAG_AGENT] Agent loop completed")
        print(f"  Turns: {turn - 1}/{MAX_AGENT_TURNS}")
        print(f"  Question: {question}")
        print(f"  Final answer: {state.final_answer or 'Not resolved'}")
        if state.eval_feedback:
            print(f"  Judge score: Accuracy={state.eval_feedback.accuracy}, Completeness={state.eval_feedback.completeness}, Relevance={state.eval_feedback.relevance}")
        print("-" * 80)
        print("[DEBUG_RAG_AGENT] Reasoning History:")
        print(state.react_history or "(empty)")
        print("=" * 80)

    return state.final_answer or "", state.context_chunks()


@retry(wait=wait)
def answer_question(
    question: str,
    history: list[dict[str, str]] | None = None,
) -> tuple[str, list[Result]]:
    """
    Answer a question using the agentic RAG pipeline and return the answer plus retrieved context.
    """
    final_answer, context = run_agent(
        question,
        history,
    )
    if final_answer:
        return final_answer, context
    fallback = "Unable to determine a suitable answer right now. Please try rephrasing your question."
    return fallback, context
