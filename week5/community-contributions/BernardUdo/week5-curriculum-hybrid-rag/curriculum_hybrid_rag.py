from __future__ import annotations

"""Hybrid RAG assistant for Week 5 community contribution.

Design goals:
- Keep retrieval grounded in local knowledge files.
- Keep operations affordable with conservative token caps.
- Provide transparent quality feedback for each answer.
"""

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from dotenv import load_dotenv
from openai import APIStatusError, OpenAI


EMBEDDING_MODEL = "openai/text-embedding-3-small"
ANSWER_MODEL = "openai/gpt-4.1-mini"
JUDGE_MODEL = "openai/gpt-4.1-nano"
TOP_K = 6
ANSWER_MAX_TOKENS = 1200
JUDGE_MAX_TOKENS = 350
LOCAL_EMBEDDING_DIM = 256
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "docs", "for", "from",
    "how", "in", "is", "it", "of", "on", "or", "that", "the", "this", "to",
    "what", "when", "where", "which", "who", "with", "according",
}


@dataclass
class ChunkRecord:
    chunk_id: str
    source: str
    text: str


@dataclass
class RetrievalHit:
    score: float
    vector_score: float
    keyword_score: float
    chunk: ChunkRecord


@dataclass
class EvalReport:
    groundedness: int
    completeness: int
    citation_quality: int
    feedback: str
    should_refine: bool


class HybridRagAssistant:
    """Hybrid vector+keyword retriever with iterative answer refinement."""

    def __init__(
        self,
        artifacts_dir: Path,
        embedding_model: str = EMBEDDING_MODEL,
        answer_model: str = ANSWER_MODEL,
        judge_model: str = JUDGE_MODEL,
        top_k: int = TOP_K,
    ) -> None:
        self.artifacts_dir = artifacts_dir
        self.embedding_model = embedding_model
        self.answer_model = answer_model
        self.judge_model = judge_model
        self.top_k = top_k
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "Missing API key. Set OPENROUTER_API_KEY in your environment or .env file."
            )
        self.client = OpenAI(
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=api_key,
        )
        self.chunks: list[ChunkRecord] = []
        self.embeddings: np.ndarray | None = None
        self.using_local_embeddings = False

    def build_index(self, source_dir: Path, chunk_chars: int = 900, overlap_chars: int = 180) -> None:
        """Create chunk and embedding artifacts from source documents."""
        files = self._collect_files(source_dir)
        if not files:
            raise ValueError(f"No source files found under {source_dir}")

        chunks: list[ChunkRecord] = []
        for file_path in files:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            for idx, chunk in enumerate(self._chunk_text(text, chunk_chars, overlap_chars), start=1):
                chunks.append(
                    ChunkRecord(
                        chunk_id=f"{file_path.name}-c{idx}",
                        source=file_path.as_posix(),
                        text=chunk,
                    )
                )

        vectors = self._embed_texts([c.text for c in chunks])
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        np.save(self.artifacts_dir / "embeddings.npy", vectors.astype(np.float32))
        (self.artifacts_dir / "chunks.json").write_text(
            json.dumps([asdict(c) for c in chunks], indent=2, ensure_ascii=True),
            encoding="utf-8",
        )
        self.chunks = chunks
        self.embeddings = self._normalize(vectors)

    def load_index(self) -> None:
        """Load previously saved chunk metadata and embedding vectors."""
        chunks_path = self.artifacts_dir / "chunks.json"
        embeddings_path = self.artifacts_dir / "embeddings.npy"
        if not chunks_path.exists() or not embeddings_path.exists():
            raise FileNotFoundError(
                f"Missing index artifacts in {self.artifacts_dir}. Run `index` first."
            )
        chunk_rows = json.loads(chunks_path.read_text(encoding="utf-8"))
        self.chunks = [ChunkRecord(**row) for row in chunk_rows]
        self.embeddings = self._normalize(np.load(embeddings_path))
        self.using_local_embeddings = (
            self.embeddings.ndim == 2 and self.embeddings.shape[1] == LOCAL_EMBEDDING_DIM
        )

    def retrieve(self, query: str, top_k: int | None = None, keyword_weight: float = 0.25) -> list[RetrievalHit]:
        """Run hybrid retrieval and return ranked hits."""
        if self.embeddings is None or not self.chunks:
            raise RuntimeError("Index is not loaded.")

        query_embedding = self._embed_texts([query])[0]
        query_norm = self._normalize(np.array([query_embedding], dtype=np.float32))[0]
        vector_scores = self.embeddings @ query_norm
        keyword_scores = np.array([self._keyword_score(query, c.text) for c in self.chunks], dtype=np.float32)
        if self.using_local_embeddings:
            # In fallback mode, rely more on lexical overlap for relevance.
            keyword_weight = 0.8
        combined = (1.0 - keyword_weight) * vector_scores + keyword_weight * keyword_scores
        if self.using_local_embeddings:
            query_terms = self._query_terms(query)
            if query_terms:
                overlap_mask = np.array(
                    [bool(query_terms.intersection(self._query_terms(c.text))) for c in self.chunks],
                    dtype=bool,
                )
                combined = np.where(overlap_mask, combined, -1.0)

        k = top_k or self.top_k
        ranked_idx = np.argsort(-combined)[:k]
        hits: list[RetrievalHit] = []
        for idx in ranked_idx:
            hits.append(
                RetrievalHit(
                    score=float(combined[idx]),
                    vector_score=float(vector_scores[idx]),
                    keyword_score=float(keyword_scores[idx]),
                    chunk=self.chunks[int(idx)],
                )
            )
        return hits

    def answer(
        self, question: str, history: list[dict[str, str]] | None = None, max_refinements: int = 2
    ) -> tuple[str, list[RetrievalHit], EvalReport]:
        """Answer a question, auditing quality and refining retrieval when needed."""
        current_query = question
        best_answer = ""
        best_hits: list[RetrievalHit] = []
        report = EvalReport(1, 1, 1, "No evaluation ran.", True)

        for attempt in range(max_refinements + 1):
            k = self.top_k + attempt * 2
            hits = self.retrieve(current_query, top_k=k)
            prompt = self._answer_prompt(question, hits, history or [])
            try:
                answer_text = self._chat(
                    self.answer_model,
                    prompt,
                    temperature=0.2,
                    max_tokens=ANSWER_MAX_TOKENS,
                )
            except APIStatusError as exc:
                if self._is_credit_error(exc):
                    fallback = self._fallback_answer_from_hits(question, hits)
                    fallback_report = self._fallback_report_from_hits(hits, str(exc))
                    return fallback, hits, fallback_report
                raise

            try:
                report = self.evaluate_answer(question, answer_text, hits)
            except APIStatusError as exc:
                if self._is_credit_error(exc):
                    # Keep generated answer even if judge model cannot run due credits.
                    report = self._fallback_report_from_hits(hits, str(exc))
                else:
                    raise
            best_answer = answer_text
            best_hits = hits
            if not report.should_refine:
                break
            current_query = self._refine_query(question, report.feedback)

        return best_answer, best_hits, report

    def evaluate_answer(self, question: str, answer_text: str, hits: list[RetrievalHit]) -> EvalReport:
        """Score answer quality based on retrieved evidence and citations."""
        citations = "\n".join(f"- [{hit.chunk.source}#{hit.chunk.chunk_id}]" for hit in hits)
        context = self._context_block(hits)
        system_prompt = (
            "You are an answer quality auditor. Score only based on provided context.\n"
            "Return strict JSON with keys: groundedness, completeness, citation_quality, feedback, should_refine.\n"
            "Scores are integers 1-5. should_refine is true when any score < 4."
        )
        user_prompt = (
            f"Question:\n{question}\n\n"
            f"Answer:\n{answer_text}\n\n"
            f"Available citations:\n{citations}\n\n"
            f"Context snippets:\n{context}\n"
        )
        raw = self._chat(
            self.judge_model,
            user_prompt,
            system_prompt=system_prompt,
            temperature=0.0,
            max_tokens=JUDGE_MAX_TOKENS,
        )
        parsed = self._safe_json(raw)
        if parsed:
            return EvalReport(
                groundedness=self._clamp_score(parsed.get("groundedness", 1)),
                completeness=self._clamp_score(parsed.get("completeness", 1)),
                citation_quality=self._clamp_score(parsed.get("citation_quality", 1)),
                feedback=str(parsed.get("feedback", "No feedback provided.")),
                should_refine=bool(parsed.get("should_refine", True)),
            )

        # Fallback heuristic in case model response is not valid JSON.
        return EvalReport(
            groundedness=3,
            completeness=3,
            citation_quality=2,
            feedback="Judge output was not valid JSON; refine retrieval and ensure explicit citations.",
            should_refine=True,
        )

    def _answer_prompt(
        self, question: str, hits: list[RetrievalHit], history: list[dict[str, str]]
    ) -> str:
        history_block = "\n".join([f"{m['role']}: {m['content']}" for m in history[-6:]]) or "None"
        context = self._context_block(hits)
        return (
            "You are a grounded knowledge assistant.\n"
            "Rules:\n"
            "1) Answer only with information present in context.\n"
            "2) If uncertain, state what is missing.\n"
            "3) Add inline citations using [source#chunk_id].\n"
            "4) When multiple chunks support the same claim, cite at least 2 sources.\n"
            "5) Prefer complete synthesis: include core mission/goal qualifiers if present (for example innovation, domain expertise, user impact).\n"
            "6) Keep the final answer concise and practical.\n\n"
            f"Conversation history:\n{history_block}\n\n"
            f"Question:\n{question}\n\n"
            f"Retrieved context:\n{context}\n"
        )

    def _refine_query(self, question: str, feedback: str) -> str:
        """Rewrite the query to recover from weak retrieval/evaluation."""
        prompt = (
            "Rewrite the search query to improve retrieval quality.\n"
            "Return only the rewritten query in one line.\n\n"
            f"Original question: {question}\n"
            f"Audit feedback: {feedback}\n"
        )
        rewritten = self._chat(
            self.judge_model,
            prompt,
            temperature=0.0,
            max_tokens=120,
        ).strip()
        return rewritten or question

    @staticmethod
    def _is_credit_error(exc: APIStatusError) -> bool:
        return exc.status_code == 402

    def _fallback_answer_from_hits(self, question: str, hits: list[RetrievalHit]) -> str:
        """Generate an extractive answer when model generation is unavailable."""
        if not hits:
            return (
                "I cannot generate a model-based answer right now, and no local evidence "
                "was retrieved for this question."
            )

        query_terms = self._query_terms(question)
        preferred = sorted(
            hits,
            key=lambda h: (
                0 if "/company/" in h.chunk.source.replace("\\", "/").lower() else 1,
                -h.score,
            ),
        )
        snippets: list[tuple[str, str]] = []
        for hit in preferred[:5]:
            source_ref = f"[{hit.chunk.source}#{hit.chunk.chunk_id}]"
            sentences = re.split(r"(?<=[.!?])\s+", hit.chunk.text.strip())
            selected = None
            for sentence in sentences:
                if len(sentence) < 30:
                    continue
                if query_terms.intersection(self._query_terms(sentence)):
                    selected = sentence
                    break
            if not selected and sentences:
                selected = sentences[0]
            if selected:
                snippets.append((selected.strip(), source_ref))
            if len(snippets) >= 2:
                break

        if not snippets:
            top = preferred[0]
            return (
                f"From local documents: {top.chunk.text[:260].strip()}... "
                f"[{top.chunk.source}#{top.chunk.chunk_id}]"
            )

        parts = [f"{text} {ref}" for text, ref in snippets]
        return " ".join(parts)

    @staticmethod
    def _fallback_report_from_hits(hits: list[RetrievalHit], err: str) -> EvalReport:
        top_score = hits[0].score if hits else 0.0
        groundedness = 4 if top_score >= 0.55 else 3
        completeness = 3 if len(hits) >= 4 else 2
        citation_quality = 4 if len(hits) >= 3 else 3
        return EvalReport(
            groundedness=groundedness,
            completeness=completeness,
            citation_quality=citation_quality,
            feedback=(
                "Fallback audit generated without LLM judge due to provider/API issue. "
                f"Top retrieval score={top_score:.3f}, retrieved_chunks={len(hits)}. "
                f"Provider error: {err}"
            ),
            should_refine=False,
        )

    @staticmethod
    def _openrouter_headers() -> dict[str, str]:
        """Build attribution headers expected by OpenRouter."""
        return {
            "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://localhost"),
            "X-Title": os.getenv("OPENROUTER_APP_NAME", "week5-curriculum-hybrid-rag"),
        }

    def _chat(
        self,
        model: str,
        user_prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        attempt_tokens = max_tokens
        min_tokens = 120
        while True:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=attempt_tokens,
                    extra_headers=self._openrouter_headers(),
                )
                return (response.choices[0].message.content or "").strip()
            except APIStatusError as exc:
                err_text = str(exc).lower()
                # Gracefully degrade completion length for low-credit OpenRouter keys.
                if exc.status_code == 402 and "fewer max_tokens" in err_text and attempt_tokens > min_tokens:
                    attempt_tokens = max(min_tokens, attempt_tokens // 2)
                    continue
                raise

    @staticmethod
    def _collect_files(source_dir: Path) -> list[Path]:
        exts = {".md", ".txt"}
        return [p for p in source_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts]

    @staticmethod
    def _chunk_text(text: str, chunk_chars: int, overlap_chars: int) -> list[str]:
        cleaned = re.sub(r"\s+", " ", text).strip()
        if not cleaned:
            return []
        chunks: list[str] = []
        start = 0
        while start < len(cleaned):
            end = min(start + chunk_chars, len(cleaned))
            chunk = cleaned[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end == len(cleaned):
                break
            start = max(0, end - overlap_chars)
        return chunks

    def _embed_texts(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        try:
            vectors: list[list[float]] = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                result = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=batch,
                    extra_headers=self._openrouter_headers(),
                )
                if not result.data:
                    raise RuntimeError("No embedding data received from provider.")
                vectors.extend([row.embedding for row in result.data])
            self.using_local_embeddings = False
            return np.array(vectors, dtype=np.float32)
        except Exception:
            # Fallback keeps notebook and CLI usable when provider credits are low
            # or embeddings endpoint is temporarily unavailable.
            self.using_local_embeddings = True
            return self._local_embed_texts(texts)

    @staticmethod
    def _local_embed_texts(texts: list[str], dim: int = LOCAL_EMBEDDING_DIM) -> np.ndarray:
        """Create deterministic, lightweight local embeddings as a fallback."""
        vectors: list[np.ndarray] = []
        for text in texts:
            vec = np.zeros(dim, dtype=np.float32)
            for token in re.findall(r"[A-Za-z0-9_]+", text.lower()):
                vec[hash(token) % dim] += 1.0
            vectors.append(vec)
        return np.array(vectors, dtype=np.float32)

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vectors / norms

    @staticmethod
    def _keyword_score(query: str, text: str) -> float:
        q_tokens = HybridRagAssistant._query_terms(query)
        t_tokens = HybridRagAssistant._query_terms(text)
        if not q_tokens:
            return 0.0
        overlap = q_tokens.intersection(t_tokens)
        return len(overlap) / len(q_tokens)

    @staticmethod
    def _query_terms(text: str) -> set[str]:
        tokens = set(re.findall(r"[A-Za-z0-9_]+", text.lower()))
        return {t for t in tokens if len(t) > 2 and t not in STOPWORDS}

    @staticmethod
    def _safe_json(raw: str) -> dict[str, Any] | None:
        raw = raw.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if not match:
                return None
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None

    @staticmethod
    def _clamp_score(value: Any) -> int:
        try:
            ivalue = int(value)
        except (TypeError, ValueError):
            ivalue = 1
        return min(5, max(1, ivalue))

    @staticmethod
    def _context_block(hits: list[RetrievalHit]) -> str:
        blocks = []
        for hit in hits:
            ref = f"[{hit.chunk.source}#{hit.chunk.chunk_id}]"
            blocks.append(f"{ref}\n{hit.chunk.text}\n")
        return "\n".join(blocks)


def run_cli(args: argparse.Namespace) -> None:
    project_dir = Path(__file__).resolve().parent
    artifacts_dir = Path(args.artifacts_dir).resolve() if args.artifacts_dir else project_dir / "artifacts"
    # Resolve default knowledge base relative to repository root, not current shell cwd.
    default_source_dir = project_dir.parents[3] / "week5" / "knowledge-base"
    source_dir = Path(args.source_dir).resolve() if args.source_dir else default_source_dir.resolve()

    assistant = HybridRagAssistant(
        artifacts_dir=artifacts_dir,
        embedding_model=args.embedding_model,
        answer_model=args.answer_model,
        judge_model=args.judge_model,
        top_k=args.top_k,
    )

    if args.command == "index":
        assistant.build_index(source_dir)
        print(f"Index created with {len(assistant.chunks)} chunks at {artifacts_dir}")
        return

    assistant.load_index()
    if args.command == "ask":
        answer_text, hits, report = assistant.answer(args.question)
        print("\nAnswer:\n")
        print(answer_text)
        print("\nRetrieved Sources:")
        for hit in hits:
            print(f"- {hit.chunk.source}#{hit.chunk.chunk_id} (score={hit.score:.3f})")
        print(
            f"\nAudit scores: groundedness={report.groundedness}, "
            f"completeness={report.completeness}, citation_quality={report.citation_quality}"
        )
        print(f"Audit feedback: {report.feedback}")
        return

    if args.command == "chat":
        history: list[dict[str, str]] = []
        print("Interactive chat started. Type 'exit' to quit.\n")
        while True:
            question = input("You: ").strip()
            if not question:
                continue
            if question.lower() in {"exit", "quit"}:
                break
            answer_text, _, report = assistant.answer(question, history=history)
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": answer_text})
            print(f"\nAssistant: {answer_text}\n")
            print(
                f"[audit] groundedness={report.groundedness} "
                f"completeness={report.completeness} citation_quality={report.citation_quality}\n"
            )
        return

    if args.command == "ui":
        import gradio as gr

        memory: list[dict[str, str]] = []

        def chat_fn(message: str, chat_history: list[tuple[str, str]]) -> str:
            del chat_history  # Gradio history is not required in this implementation.
            answer_text, _, report = assistant.answer(message, history=memory)
            memory.append({"role": "user", "content": message})
            memory.append({"role": "assistant", "content": answer_text})
            return (
                f"{answer_text}\n\n"
                f"_audit: groundedness={report.groundedness}, completeness={report.completeness}, "
                f"citation_quality={report.citation_quality}_"
            )

        demo = gr.ChatInterface(
            fn=chat_fn,
            title="Week 5 Curriculum Hybrid RAG Assistant",
            description="Grounded QA with hybrid retrieval and self-audit scores.",
        )
        demo.launch()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Week 5 community contribution: Hybrid RAG assistant")
    parser.add_argument("--artifacts-dir", default=None, help="Path to save/load index artifacts")
    parser.add_argument("--source-dir", default=None, help="Knowledge source directory for indexing")
    parser.add_argument("--embedding-model", default=EMBEDDING_MODEL, help="Embedding model name")
    parser.add_argument("--answer-model", default=ANSWER_MODEL, help="Answer generation model")
    parser.add_argument("--judge-model", default=JUDGE_MODEL, help="Evaluation model")
    parser.add_argument("--top-k", type=int, default=TOP_K, help="Number of retrieved chunks")

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("index", help="Build embeddings index from source files")

    ask = sub.add_parser("ask", help="Ask one question")
    ask.add_argument("--question", required=True, help="Question to answer")

    sub.add_parser("chat", help="Start interactive CLI chat")
    sub.add_parser("ui", help="Launch Gradio chat UI")
    return parser


def main() -> None:
    load_dotenv(override=True)
    parser = build_parser()
    args = parser.parse_args()
    if not (os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")):
        raise EnvironmentError(
            "Missing API key. Set OPENROUTER_API_KEY (or OPENAI_API_KEY) in your environment or .env file."
        )
    run_cli(args)


if __name__ == "__main__":
    main()
