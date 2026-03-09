import json
from dotenv import load_dotenv
from litellm import completion

from tools import (
    search_knowledge_base,
    search_arxiv_papers,
    ingest_papers,
    get_paper_details,
    Result,
)

load_dotenv(override=True)

MODEL = "openai/gpt-4.1-mini"
MAX_ITERATIONS = 15

SYSTEM_PROMPT = """\
You are an intelligent arXiv research assistant with access to tools for \
searching and analysing academic papers.

## Capabilities
1. **search_knowledge_base** — find relevant chunks from pre-ingested arXiv papers
2. **search_arxiv** — discover new papers on any topic via the arXiv API
3. **ingest_papers** — add new papers to the knowledge base for detailed Q&A
4. **get_paper_details** — fetch full metadata for a specific paper

## Strategy
- For questions about known topics, start with `search_knowledge_base`.
- If results are insufficient or empty, rephrase the query or try \
`search_arxiv` to find new papers.
- For new / unfamiliar topics, `search_arxiv` first, then `ingest_papers` \
for the most relevant hits, then `search_knowledge_base`.
- For paper comparisons, make multiple targeted searches.
- Break complex questions into sub-queries and search multiple times.
- Always cite paper titles and URLs when referencing specific findings.
- If you genuinely cannot find relevant information after trying multiple \
approaches, say so honestly.

## Response Style
- Be technically precise and concise.
- Use markdown formatting for clarity.
- Cite sources with paper titles and links.
- When synthesising across papers, clearly attribute each finding to its \
source paper."""

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the local knowledge base of ingested arXiv papers "
                "for relevant chunks. Use this to find information in papers "
                "that have already been ingested."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant paper chunks",
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of results to return (default 10)",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_arxiv",
            "description": (
                "Search arXiv for papers on a topic. Returns titles, "
                "abstracts, and URLs. Use this when the user asks about "
                "topics not well covered by ingested papers, or to discover "
                "new research."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query for arXiv",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of papers to return (default 5)",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ingest_papers",
            "description": (
                "Ingest arXiv papers into the knowledge base by downloading "
                "PDFs, extracting text, chunking, and storing embeddings. "
                "Use this after search_arxiv when you want to make papers "
                "available for detailed Q&A."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "arxiv_urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of arXiv paper URLs to ingest",
                    },
                },
                "required": ["arxiv_urls"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_paper_details",
            "description": (
                "Get detailed metadata for a specific arXiv paper including "
                "title, authors, abstract, categories, and publication date."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "arxiv_url": {
                        "type": "string",
                        "description": "The arXiv URL or ID of the paper",
                    },
                },
                "required": ["arxiv_url"],
            },
        },
    },
]

TOOL_MAP = {
    "search_knowledge_base": search_knowledge_base,
    "search_arxiv": search_arxiv_papers,
    "ingest_papers": ingest_papers,
    "get_paper_details": get_paper_details,
}


def _format_tool_result(name: str, result) -> str:
    """Serialise a tool's return value into text the LLM can reason over."""
    if name == "search_knowledge_base":
        if not result:
            return "No results found in the knowledge base."
        parts = []
        for i, chunk in enumerate(result, 1):
            meta = chunk.metadata
            parts.append(
                f"[{i}] **{meta.get('title', 'Unknown')}** "
                f"({meta.get('arxiv_url', '')})\n"
                f"Category: {meta.get('primary_category', 'N/A')} | "
                f"Published: {meta.get('published', 'N/A')}\n"
                f"{chunk.page_content[:500]}"
            )
        return (
            f"Found {len(result)} relevant chunks:\n\n"
            + "\n\n---\n\n".join(parts)
        )

    if name == "search_arxiv":
        if not result:
            return "No papers found on arXiv for this query."
        parts = []
        for i, paper in enumerate(result, 1):
            authors = ", ".join(paper["authors"][:5])
            parts.append(
                f"[{i}] **{paper['title']}**\n"
                f"Authors: {authors}\n"
                f"URL: {paper['arxiv_url']}\n"
                f"Category: {paper['primary_category']} | "
                f"Published: {paper['published'][:10]}\n"
                f"Abstract: {paper['summary'][:300]}..."
            )
        return (
            f"Found {len(result)} papers:\n\n"
            + "\n\n---\n\n".join(parts)
        )

    return json.dumps(result, default=str)


def run_agent(
    user_message: str,
    history: list[dict] | None = None,
) -> tuple[str, list[Result], list[dict]]:
    """Execute the agent loop.

    Returns (final_answer, retrieved_chunks, tool_log).
    """
    history = history or []
    retrieved_chunks: list[Result] = []
    tool_log: list[dict] = []

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    for _ in range(MAX_ITERATIONS):
        response = completion(
            model=MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )
        choice = response.choices[0]

        if not choice.message.tool_calls:
            return choice.message.content or "", retrieved_chunks, tool_log

        messages.append(choice.message.model_dump())

        for tool_call in choice.message.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)
            tool_log.append({"tool": fn_name, "args": fn_args})

            fn = TOOL_MAP.get(fn_name)
            if fn is None:
                result = f"Unknown tool: {fn_name}"
            else:
                try:
                    result = fn(**fn_args)
                except Exception as exc:
                    result = f"Tool error: {exc}"

            if fn_name == "search_knowledge_base" and isinstance(result, list):
                retrieved_chunks.extend(result)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": _format_tool_result(fn_name, result),
                }
            )

    return (
        "I reached the maximum number of reasoning steps. "
        "Here is what I found so far based on my research.",
        retrieved_chunks,
        tool_log,
    )
