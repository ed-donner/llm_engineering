# 🍻 Three Frontier Models Walk Into a Bar

A fun multi-agent experiment inspired by the *Mastering LLM Engineering* course.

This project simulates a lively philosophical debate between three frontier language models:

- GPT-4.1 Mini (the skeptical atheist)
- Claude Haiku 4.5 (the stubborn religious believer)
- OpenRouter Free Router (the indecisive mediator)

Each model is assigned a distinct personality and worldview and participates in a shared conversation using a common transcript. The result is an entertaining demonstration of multi-agent orchestration where LLMs interact with each other rather than simply responding to a human prompt.

---

## 🎯 Goal

The objective of this project is to explore:

- Multi-agent systems
- Shared conversational memory
- Agent personalities via system prompts
- OpenAI-compatible APIs
- Context management and orchestration

Rather than building a chatbot, this exercise turns the models into autonomous participants in an ongoing discussion.

---

## 🏗️ Architecture

The project uses a shared-state architecture.

```text
Shared Conversation Transcript
                │
                ▼
      ┌─────────────────┐
      │      GPT        │
      └─────────────────┘
                │
                ▼
      ┌─────────────────┐
      │     Claude      │
      └─────────────────┘
                │
                ▼
      ┌─────────────────┐
      │   OpenRouter    │
      └─────────────────┘
                │
                ▼
    Updated Transcript
```

Each model:

1. Reads the complete conversation history.
2. Interprets its own previous messages as `assistant`.
3. Interprets all other participants as `user`.
4. Generates a response.
5. Appends its response to the shared transcript.

---

## 🧠 Agent Personalities

### GPT

**Role:** Skeptical Atheist

- Relies on science and evidence
- Challenges unsupported claims
- Enjoys debate
- Prioritizes reason and empirical thinking

### Claude

**Role:** Religious Believer

- Deeply committed to faith
- Defends spiritual explanations
- Resistant to scientific critiques
- Frequently attempts to justify beliefs

### OpenRouter

**Role:** Indecisive Mediator

- Unsure what to believe
- Easily influenced by both sides
- Genuinely curious
- Attempts to find common ground

---

## 📋 Conversation State

The conversation is maintained in a shared transcript:

```python
conversation = [
    ("GPT", "Hi there!"),
    ("Claude", "Hi!"),
    ("OpenRouter", "Hi!")
]
```

This transcript acts as the single source of truth for the discussion.

Each model reconstructs its own context from this transcript before generating a reply.

For example, GPT's message history is built like this:

```python
messages = [
    {"role": "system", "content": gpt_system}
]

for speaker, text in conversation:

    if speaker == "GPT":
        role = "assistant"
    else:
        role = "user"

    messages.append({
        "role": role,
        "content": f"{speaker}: {text}"
    })
```

This allows GPT to view its own previous messages as assistant outputs while treating the other models as conversational participants.

---

## 🔄 Conversation Loop

The orchestrator cycles through the three models:

```python
agents = [
    ("GPT", call_gpt),
    ("Claude", call_claude),
    ("OpenRouter", call_openrouter)
    ]

for _ in range(NUM_ROUNDS):
    random.shuffle(agents)
    for name, func in agents:
        func()
```

Each reply is appended to the shared transcript:

```python
conversation.append(("GPT", gpt_reply))
conversation.append(("Claude", claude_reply))
conversation.append(("OpenRouter", openrouter_reply))
```

Randomizing speaker order prevents any single model from consistently having the first or last word and produces more natural interactions.
The initial version generates approximately:
- 5 GPT responses
- 5 Claude responses
- 5 OpenRouter responses

plus the opening greetings.

This creates a more realistic group conversation where debate dynamics evolve differently on every run..

---

## 🐛 Interesting Emergent Behavior

One unexpected behavior appeared after several rounds.

The models began generating responses like:

```text
GPT says:
...
```

or

```text
Claude says:
...
```

even though they were never explicitly instructed to do so. This happened because the models learned formatting patterns from the transcript and began mimicking them.

This provided a valuable lesson:

> Context becomes part of the prompt.

The issue was fixed by:
- Explicitly telling each model not to identify itself.

---

## 🚀 Future Ideas

Potential improvements include:

- Adding Gemini, DeepSeek, Grok, and other models
- Debate judging and scoring
- Belief updates over time
- Long-term memory and summarization
- Tournament-style debates
- Expert-panel simulations

For example:

```text
Climate Scientist
Energy Economist
Policy Maker
Skeptical Journalist
```

---

## ⚠️ Disclaimer

This project is intended as a learning exercise in:

- Multi-agent orchestration
- Prompt engineering
- Shared conversational memory
- LLM behavior analysis

The viewpoints expressed by the agents are fictional personas created solely to encourage debate and explore model interactions. They do not represent the views of the model providers or the author.

---