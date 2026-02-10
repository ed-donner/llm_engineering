# Week 5 Challenge: Agentic RAG

This is an agentic (ReAct-style) RAG implementation that improves upon the static RAG from the base Week 5 course. Instead of a single retrieval pass, the system uses a controller agent that iteratively refines answers through retrieval and self-evaluation.

## Architecture

The agent follows a ReAct (Reasoning + Acting) loop:

```
User Question
    ↓
┌─────────────────────────────────────┐
│  ReAct Loop (up to 15 turns)        │
│                                     │
│  Thought → Action → Observation     │
│                                     │
│  Tools:                             │
│  - vector_search: semantic search   │
│  - text_search: keyword search      │
│  - rerank: reorder chunks           │
│  - judge_answer: evaluate draft     │
│  - final_answer: submit response    │
└─────────────────────────────────────┘
    ↓
Final Answer + Retrieved Chunks
```

The agent must call `judge_answer` to evaluate its draft answer. Only when scores meet thresholds (Accuracy=5, Relevance=5, Completeness≥4) can it call `final_answer`.

## Setup

```bash
cd week5/community-contributions/week5-challenge-agentic-rag

# Install dependencies
uv pip install -e .

# Create .env file with required API keys
echo "OPENAI_API_KEY=your-key-here" > .env
echo "GROQ_API_KEY=your-key-here" >> .env
```

## Debug Logging Levels

Set `DEBUG_RAG_AGENT` to control agent logging verbosity:

| Level | Output |
|-------|--------|
| `0` | Silent - no debug output |
| `1` | Agent loop summary only - shows turns, question, final answer, and full reasoning history on loop exit |
| `2` | Operational logs - turn info, selected actions, observations, errors |
| `3` | Prompts - includes the user prompt sent to the LLM each turn |
| `4` | Full LLM responses - complete JSON response from model |

Level 1 output example:
```
================================================================================
[DEBUG_RAG_AGENT] Agent loop completed
  Turns: 4/15
  Question: Who founded Insurellm?
  Final answer: Avery Lancaster founded Insurellm in 2015.
  Judge score: Accuracy=5.0, Completeness=5.0, Relevance=5.0
--------------------------------------------------------------------------------
[DEBUG_RAG_AGENT] Reasoning History:
Thought: I need to find information about who founded Insurellm...
Action: vector_search
Action Input: {"query": "Who founded Insurellm?"}
Observation: Retrieved 20 chunks...
...
================================================================================
```