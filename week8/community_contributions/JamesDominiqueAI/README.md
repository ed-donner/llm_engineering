# ⬡ Prism — Multi-Agent Research System

> Three AI analysts research in parallel. One synthesis engine unifies the truth.

A fully agentic multi-agent research pipeline built with Python and Gradio.
Submit a single query and watch **Claude**, **GPT-4o**, and **Gemini** each run
their own autonomous research loop — searching the live web, reasoning over
results, and writing independent reports — then a GPT-4o synthesis agent
cross-references all three, identifies consensus and disagreements, and
produces a single authoritative intelligence brief.

---

## Architecture

```
Your Query
    │
    ├─────────────────────────────────────────────────┐
    │                      │                          │
    ▼                      ▼                          ▼
Agent 1                Agent 2                    Agent 3
Claude                 GPT-4o                     Gemini
(Anthropic)            (OpenAI)                (OpenRouter)
    │                      │                          │
Anthropic            DuckDuckGo                 DuckDuckGo
web_search tool       function                   function
    │                  calling                    calling
    │                      │                          │
 Agentic loop ×8       Agentic loop ×8           Agentic loop ×8
 ┌──────────┐           ┌──────────┐              ┌──────────┐
 │ Search   │           │ Search   │              │ Search   │
 │ Store    │           │ Retrieve │              │ Retrieve │
 │ Reason   │           │ Reason   │              │ Reason   │
 │ Repeat   │           │ Repeat   │              │ Repeat   │
 └──────────┘           └──────────┘              └──────────┘
    │                      │                          │
    └─────────────────────────────────────────────────┘
                           │
                    (all 3 run in parallel threads)
                           │
                           ▼
                   Synthesis Agent
                     GPT-4o
             ┌──────────────────────┐
             │  Compare 3 reports   │
             │  Find consensus      │
             │  Flag disagreements  │
             │  Write final report  │
             └──────────────────────┘
                           │
                           ▼
               Unified Intelligence Report
```

---

## What Makes It Truly Agentic

All three research agents now run the same **autonomous decision loop**:

```
while not done:
    model decides what to search next     ← LLM drives the loop
    tool executes the search              ← real web data
    results fed back into conversation    ← growing context
    model decides: search more or write?  ← autonomous decision
    if searched < 4 times: nudge model    ← self-correction
write report from live evidence           ← grounded output
```

