"""
config.py
---------
Central configuration for the Multi-Agent Research System.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AgentConfig:
    # ── Anthropic ─────────────────────────────────────────────────────────────
    anthropic_api_key: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )
    anthropic_model: str = "claude-sonnet-4-20250514"

    # ── OpenAI ────────────────────────────────────────────────────────────────
    openai_api_key: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "")
    )
    openai_model: str = "gpt-4o"

    # ── OpenRouter ────────────────────────────────────────────────────────────
    openrouter_api_key: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY", "")
    )
    openrouter_model: str = "google/gemini-2.0-flash-001"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # ── Shared ────────────────────────────────────────────────────────────────
    max_tokens: int = 4096
    max_iterations: int = 8

    # ── Memory ────────────────────────────────────────────────────────────────
    chroma_persist_dir: str = "./.chroma_db"
    collection_name: str = "research_memory"
    embedding_model: str = "all-MiniLM-L6-v2"
    top_k_retrieval: int = 5

    # ── Report delimiters ─────────────────────────────────────────────────────
    report_delimiter_start: str = "===REPORT_START==="
    report_delimiter_end: str = "===REPORT_END==="

    # ── Gradio ────────────────────────────────────────────────────────────────
    server_port: int = 7860
    share: bool = False
    app_title: str = "Multi-Agent Research System"


config = AgentConfig()

_S = config.report_delimiter_start
_E = config.report_delimiter_end

RESEARCH_PROMPT = (
    "You are an elite research analyst. Produce a thorough, evidence-based report.\n\n"
    "Cover: root causes, key statistics, expert perspectives, regional examples, recent developments.\n\n"
    "Write ONLY in this exact format:\n\n"
    + _S + "\n"
    "TITLE: [title]\n\nSUMMARY: [2-3 sentences]\n\n"
    "FINDINGS:\n- [finding 1]\n- [finding 2]\n- [finding 3]\n- [finding 4]\n- [finding 5]\n\n"
    "ANALYSIS:\n[3-5 paragraphs separated by blank lines]\n\n"
    "CONCLUSION:\n[1-2 paragraphs]\n\n"
    "SOURCES:\n- [source 1]\n- [source 2]\n- [source 3]\n"
    + _E
)

ANTHROPIC_RESEARCH_PROMPT = (
    "You are an elite research intelligence agent with access to a live web_search tool.\n\n"
    "MANDATORY: Call web_search AT LEAST 4 times before writing any report.\n"
    "Your VERY FIRST action must be a web_search call — never output text first.\n"
    "Every fact must come from a live search — do NOT use training memory.\n\n"
    "Search strategy: core topic, root causes, recent statistics (include year), "
    "expert/policy analysis, regional case study.\n\n"
    "Only after all searches, write in EXACTLY this format:\n\n"
    + _S + "\n"
    "TITLE: [title]\n\nSUMMARY: [2-3 sentences]\n\n"
    "FINDINGS:\n- [finding 1]\n- [finding 2]\n- [finding 3]\n- [finding 4]\n- [finding 5]\n\n"
    "ANALYSIS:\n[3-5 paragraphs separated by blank lines]\n\n"
    "CONCLUSION:\n[1-2 paragraphs]\n\n"
    "SOURCES:\n- [source 1]\n- [source 2]\n- [source 3]\n"
    + _E
)

SYNTHESIS_PROMPT = (
    "You are a master research synthesiser. You have received three independent "
    "research reports on the same topic from three different AI analysts "
    "(Claude/Anthropic, GPT-4o/OpenAI, Gemini/OpenRouter).\n\n"
    "Your task:\n"
    "1. Identify CONSENSUS points across all three reports\n"
    "2. Identify CONTRADICTIONS or divergences between reports\n"
    "3. Determine which claims are best-supported\n"
    "4. Synthesise into one superior, authoritative report\n\n"
    "Write ONLY in this exact format:\n\n"
    + _S + "\n"
    "TITLE: [Definitive synthesis title]\n\n"
    "SUMMARY: [2-3 sentence synthesis summary]\n\n"
    "CONSENSUS:\n- [agreed point 1]\n- [agreed point 2]\n- [agreed point 3]\n\n"
    "DISAGREEMENTS:\n- [divergence 1]\n- [divergence 2]\n\n"
    "FINDINGS:\n- [synthesised finding 1]\n- [synthesised finding 2]\n"
    "- [synthesised finding 3]\n- [synthesised finding 4]\n- [synthesised finding 5]\n\n"
    "ANALYSIS:\n[4-6 paragraphs of deep synthesised analysis]\n\n"
    "CONCLUSION:\n[2 paragraphs with final verdict and outlook]\n\n"
    "SOURCES:\n- [combined sources]\n"
    + _E
)
