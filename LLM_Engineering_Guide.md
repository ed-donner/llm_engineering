# LLM Engineering — Essential Knowledge

> Progressive guide · From first principles to production
> Every concept explained before it is used · Glossary at the end

> **How to read this.** Every capable LLM system grows along the same arc — *a plain prompt → structured, validated output → tools for what the model can't do → retrieved knowledge for what it doesn't know → a tuned model when behavior itself must change → an agent when the path can't be fixed in advance → a hardened product.* This document walks that arc. Part I is the ground it stands on — what a model is and how it works; Parts II–VI each climb one step and are reassembled in the Architecture Decision Guide (§28). To keep it concrete, one example runs the whole way: **an assistant that answers questions over a company's internal documents.** Read Parts I–II in order if you are starting from zero; Parts III–VI can be taken in any order afterward. Each Part opens by placing itself on the arc, and each ends with a checkpoint.

---

## Table of Contents

**Part I — Understanding LLMs**
1. [What Is an LLM?](#1-what-is-an-llm)
2. [How Text Generation Works](#2-how-text-generation-works)
3. [How LLMs Are Trained](#3-how-llms-are-trained)
4. [Tokenization](#4-tokenization)
5. [The Transformer](#5-the-transformer)

**Part II — Working with Models**
6. [The API Paradigm](#6-the-api-paradigm)
7. [The Model Landscape](#7-the-model-landscape)
8. [Prompt Engineering](#8-prompt-engineering)
9. [Conversations and Memory](#9-conversations-and-memory)
10. [Temperature and Output Control](#10-temperature-and-output-control)
11. [Structured Outputs](#11-structured-outputs)
12. [Tool Calling](#12-tool-calling)
13. [Multimodal Capabilities](#13-multimodal-capabilities)

**Part III — RAG**
14. [Embeddings](#14-embeddings)
15. [The RAG Pattern](#15-the-rag-pattern)
16. [Chunking](#16-chunking)
17. [Advanced Retrieval](#17-advanced-retrieval)
18. [RAG Evaluation and Failure Analysis](#18-rag-evaluation-and-failure-analysis)

**Part IV — Fine-Tuning**
19. [When to Fine-Tune](#19-when-to-fine-tune)
20. [Fine-Tuning Methods](#20-fine-tuning-methods)
21. [QLoRA — Fine-Tuning on Consumer Hardware](#21-qlora--fine-tuning-on-consumer-hardware)

**Part V — Agents**
22. [Workflows vs Agents](#22-workflows-vs-agents)
23. [Agent Architecture](#23-agent-architecture)
24. [Multi-Agent Systems](#24-multi-agent-systems)

**Part VI — Production**
25. [Evaluation](#25-evaluation)
26. [Cost Thinking](#26-cost-thinking)
27. [Security](#27-security)
28. [Architecture Decision Guide](#28-architecture-decision-guide)

**Appendices**
- [Glossary](#glossary)
- [Revision Questions](#revision-questions)
- [References](#references)

---

# Part I — Understanding LLMs

*No code, no tools, no frameworks. The goal is an intuitive understanding of what LLMs are and how they work — the kind that lets you reason about their behavior, predict their failures, and design systems around their strengths.*

---

## 1. What Is an LLM?

A **neural network** is a program made of layers of simple mathematical operations connected together. Each layer takes numbers in, transforms them, and passes numbers out. Stacked together, these layers learn complex patterns from data. A neural network trained on images learns to see; one trained on text learns to read and write.

A **Large Language Model (LLM)** is a neural network trained to predict the next piece of text given everything that came before it. When you do this prediction at enormous scale — trillions of training examples, billions of **parameters** (numerical weights adjusted during training) — the model learns grammar, facts, reasoning patterns, code syntax, and the structure of arguments, all as side effects of getting better at prediction.

An LLM is not the whole application. A useful product contains an LLM *plus* application logic, permissions, data retrieval, tool integrations, validation, and a user interface. The LLM is one component — a powerful but unreliable one that must be constrained by the system around it.

### What LLMs Cannot Do

LLMs do not access the internet, databases, or calculators unless explicitly given tools (§12). They do not learn from conversations — every call is independent. They have no truth-checking mechanism — they generate what *sounds right*, not what *is right*. And they have a hard **knowledge cutoff**: they know nothing about events after their training data was collected.

Every technique in this document — RAG, tool calling, evaluation, guardrails — exists to work around one of these limitations.

---

## 2. How Text Generation Works

### Next-Token Prediction

The core mechanism: given a sequence of **tokens** (sub-word text units, roughly a syllable each), the model assigns a probability to every possible next token, then selects one. It computes a **probability distribution** — spreading 100% of its confidence across all possible next tokens (often around 100,000). For `"The capital of France is"`, the token `"Paris"` might get 85%, `"Lyon"` 3%, `"banana"` 0.0001%. Then one token is selected based on the **temperature** setting (§10).

### Autoregressive Generation

The model generates one token, appends it to the input, and predicts again. Each prediction is conditioned on all prior tokens, including the ones the model itself just generated. This is why output appears word-by-word when streaming.

Two consequences matter. First, **errors compound** — an early wrong token contaminates everything after it, which is why hallucinations can be so elaborate. Second, **generation is slow relative to input processing** — input tokens are processed in parallel, but output tokens are produced sequentially. This is why output tokens cost more.

### The Illusion of Understanding

When GPT explains quantum mechanics, it has learned from millions of physics texts what sequences of words typically follow phrases about the topic. The output is a statistical reconstruction. This explains both its strengths (expert-level text on thousands of topics) and its failures (equally confident text about things it knows nothing about). A confident false statement is called a **hallucination**.

---

## 3. How LLMs Are Trained

### Phase 1: Pre-Training

The model reads trillions of tokens and at each step predicts the next one. Errors adjust its parameters slightly. Across trillions of predictions, it learns language, facts, reasoning, and code. The result is a powerful but undirected text predictor that will complete *any* text — including toxic or incoherent text — because it learned from the whole internet without judgment.

### Phase 2: Instruction Tuning (SFT)

The model is trained on curated (instruction, ideal response) pairs. This teaches it to behave as an assistant: answer questions, follow formatting instructions, stay on topic. The transformation is dramatic — the same model goes from unpredictable text completion to structured, useful responses.

Open-source models come in two versions: a **base model** (pre-trained only) and an **instruct model** (SFT applied). "Llama-3.2-3B-Instruct" vs "Llama-3.2-3B" is this difference.

### Phase 3: Alignment (RLHF / DPO)

Human raters rank multiple model responses. A reward model learns these preferences, then the LLM is optimized to produce preferred responses. **DPO** (Direct Preference Optimization) is a simpler alternative that skips the separate reward model. Alignment makes models refuse dangerous requests and acknowledge uncertainty — but sometimes over-refuse benign ones.

### Why This Matters for Engineering

When a model refuses an appropriate request → alignment too aggressive. When it confidently fabricates → pre-training gave patterns but not truth. When it ignores formatting → instruction tuning didn't cover that format. When a base model behaves erratically → it hasn't been instruction-tuned. Knowing which phase causes which behavior helps you diagnose problems.

### Scaling Laws and Emergent Capabilities

Model quality improves predictably with more compute, data, and parameters — but "bigger" alone doesn't guarantee better. The Chinchilla finding showed that smaller models trained on more data can outperform larger models trained on less. Some capabilities appear suddenly at certain scale thresholds, though whether these are truly "emergent" or artifacts of measurement remains debated. The practical lesson: measure the exact task rather than assuming a larger model will cross a magical threshold.

---

## 4. Tokenization

**Cost is measured in tokens.** You pay per input and output token. **Context windows are measured in tokens** — the maximum a model can process in one call. These have grown quickly: once tens of thousands of tokens, flagship windows now commonly reach ~1M, and some go far beyond. Exceeding the limit causes an error.

**Byte-Pair Encoding (BPE)**, the dominant algorithm, iteratively merges the most frequent character pairs into single tokens. Common words become one token; rare words are split into pieces. The vocabulary is fixed after training.

**Rule of thumb**: 1 token ≈ 4 characters ≈ 0.75 English words. A 128K context window holds roughly a 300-page book. Non-Latin scripts use 2–3× more tokens per word — same content costs more.

When input exceeds the context window: **truncate** (cut to fit), **summarize** (compress with a cheap model first), or **chunk** (split into overlapping pieces and process each — the foundation of RAG, §15).

---

## 5. The Transformer

Every modern LLM is based on the **Transformer** (Vaswani et al., 2017). Understanding it explains why LLMs handle long contexts, why they scale, and where their limits come from.

### Prerequisite: Vectors

A **vector** is an ordered list of numbers. `[48.86, 2.35]` represents Paris (latitude, longitude). `[255, 128, 0]` represents orange (red, green, blue). Inside a Transformer, every token is represented as a vector of hundreds of numbers. The model learns during training what each dimension should encode. Similar meanings → similar vectors.

### The Problem Before Transformers

**Recurrent Neural Networks (RNNs)** processed text sequentially — one token at a time. During training, the model learns by sending correction signals (**gradients**) backward through the network. In RNNs, these gradients shrink at each sequential step (**vanishing gradients**), so by token 500, the signal from token 1 has disappeared. The model cannot learn long-range relationships. Sequential processing is also slow.

### Attention: The Core Idea

The Transformer uses **self-attention** to let each token consider other relevant tokens. In *"The bank by the river was covered in moss,"* the word "bank" attends strongly to "river" and "moss," resolving the ambiguity. During prompt processing, all positions can be computed in parallel, but each position can attend only to itself and earlier positions — never to future tokens. This constraint (causal masking, detailed below) is what makes next-token prediction possible.

> *Skippable on a first read.* The subsections that follow give the mechanism and the exact formula. Nothing later in this document depends on the math — only on the idea just stated: attention lets each token pull in information from the other tokens that matter.

### How Attention Works

Each token's vector is projected into three new vectors: **Query** ("what am I looking for?"), **Key** ("what do I contain?"), and **Value** ("what information do I carry?"). The model computes a **dot product** (multiply corresponding numbers, add the results) between every Query and every Key, producing relevance scores. These are passed through **softmax** (a function that converts any list of numbers into positive values that sum to 1 — e.g., raw scores `[3.0, 0.5, -0.5]` become `[0.90, 0.07, 0.03]`). The probabilities then weight a blend of all Values. Result: each token's representation now incorporates information from every relevant token.

The formula: `Attention(Q, K, V) = softmax(QKᵀ / √d_k) · V`. The `√d_k` keeps scores in a reasonable range so softmax doesn't collapse to attending to only one token.

### Multi-Head Attention

Language has many simultaneous relationships: syntax, semantics, coreference. **Multi-head attention** runs 32–128 parallel attention computations ("heads"), each learning a different relationship type. One head might track subject-verb agreement; another might track which noun a pronoun refers to. Their outputs combine into a rich representation.

### A Transformer Layer

A single layer has two stages. **Self-attention** (multi-head) routes information between tokens. Then a **Feed-Forward Network (FFN)** — a small neural network each token passes through independently — transforms each position's representation. FFNs appear to play an important role in storing and transforming learned associations, although knowledge is distributed throughout the network.

Each stage uses a **residual connection** (`output = input + stage(input)`) so gradients don't vanish across many layers, and **normalization** to keep numbers stable. A full Transformer stacks dozens of these layers, building progressively more abstract representations.

### Causal Masking

In decoder-only LLMs, token at position *t* can only attend to positions 0 through *t-1*. Future positions are blocked before the softmax step. During training, many positions can still be computed in parallel because the correct previous tokens are already known. During generation, new tokens must be produced one at a time.

### Encoder, Decoder, and Why It Matters

An **encoder** reads all tokens freely (bidirectionally) to build a representation — think of it as a reader. A **decoder** generates tokens one at a time with causal masking — think of it as a writer. The original Transformer used both. Modern LLMs are **decoder-only** — one architecture does both reading and writing, which scales better and is powerful enough for virtually all tasks.

| Variant | Analogy | Examples | Use |
|---|---|---|---|
| Encoder-only | Reader | BERT | Classification, embeddings |
| Decoder-only | Writer that reads as it goes | GPT, Llama, Claude | Text generation (the standard) |
| Encoder-Decoder | Reader + writer | T5, BART | Translation (largely superseded) |

---

> **Part I checkpoint.** You should be able to explain: what an LLM is and cannot do; autoregressive generation and error compounding; the three training phases; why tokens matter for cost/context; and how attention works conceptually.

---

# Part II — Working with Models

*You know what a model is; now you'll drive one. These are the first steps on the arc: turning a raw next-token predictor into a controllable component — shaping it with prompts, pinning its output to a schema, giving it tools — with the document-assistant as the testbed.*

---

## 6. The API Paradigm

You send an HTTP request with a list of messages and receive a response. There is no session, no state retained between calls.

**Message roles** determine how the model treats content. **`system`** sets persona, constraints, and rules (highest priority). **`user`** is the human's input. **`assistant`** is prior model output (reconstructs history). **`tool`** is a function result returned to the model.

**Statelessness is the most important concept.** Every call is independent. A "conversation" is an illusion your application maintains by re-sending the full message history each time. Each later call costs more than the previous one because the history grows — and across a full conversation, cumulative input cost can grow approximately quadratically unless history is summarized or trimmed.

**Interoperable interface.** Most providers offer OpenAI-compatible API layers — you can often switch providers with limited application changes, although provider-specific features, tool behavior, streaming, and error handling still differ.

**Version pinning.** Model behavior can change when a provider updates a model alias. Pin versions for reproducibility; run regression tests before migration.

---

## 7. The Model Landscape

Models differ along four axes: **capability**, **speed**, **cost**, and **context window**. No single model is best at everything.

**Frontier models** (the flagship GPT, Claude, and Gemini families) are proprietary, accessed via API, generally the most capable. **Open-weight models** (Llama, Mistral, DeepSeek) publish weights — you can run them locally, fine-tune them, deploy without per-token costs. The gap is narrowing.

**Reasoning models** spend extra hidden tokens on an internal chain-of-thought before answering — stronger on logic, math, and multi-step planning, but slower and more expensive. Increasingly this is less a separate class of model than a *mode*: modern flagships are often **hybrid reasoning models** that let you dial a "thinking budget" up or down per request. Either way, spend the extra reasoning selectively, not by default.

> **Landscape snapshot — July 2026 (perishable).** A ~1M-token context window is now ordinary across flagship models rather than a headline feature, and several go well beyond it; reasoning is increasingly a per-request budget inside one model rather than a separate product line. Specific names and numbers age in months — trust the principles in this section, not the leaderboard of the week.

**Build a model ladder.** A production system often uses several models: a cheap one for routing/extraction, a stronger one for complex cases, an embedding model for retrieval, a reranker for search precision. Match model to task.

**Running models locally.** Tools like Ollama run open-weight models on your machine. Same API interface, zero cost, fully private. Trade-off: smaller models, less capability.

---

## 8. Prompt Engineering

The most important practical skill. Everything else — RAG, fine-tuning, agents — is built on top of effective prompting.

**Context engineering** is the broader discipline: deciding what information the model receives, in what structure, order, and trust level. A "prompt" is not just the user's sentence — it is the full set of instructions, examples, context, schemas, and tool descriptions.

### The System Prompt

Your primary control surface. A vague system prompt produces vague results. A good one specifies: role (who the model is), scope (what topics are in/out), constraints (what not to do), format (how to structure output), fallback behavior (what to do when uncertain), and dynamic context (retrieved documents injected at call time).

### Prompting Techniques

**Zero-shot** — no examples, just instructions. Works for well-defined tasks.

**Few-shot** — 2–5 examples of desired input/output before the actual question. The model learns the pattern. Examples should cover edge cases, be diverse, and use the exact format you want — the model will mirror it. 3–5 is the sweet spot; more than 10 rarely helps.

**Chain-of-Thought (CoT)** — "think step by step" before answering. Dramatically improves math, logic, and multi-step problems because intermediate tokens serve as working memory. But forced CoT is not universally beneficial — reasoning models often perform better with clear goals and constraints rather than explicit chain-of-thought instructions.

**Prompt chaining** — break complex tasks into sequential focused calls, each feeding the next. More expensive, but higher quality and easier to debug. This is the architecture of every serious LLM application.

### Common Mistakes

Being too vague; asking for too many things at once; not specifying what *not* to do; mixing untrusted data with trusted instructions; changing prompts without regression tests; expecting prompting to compensate for missing knowledge (use RAG) or missing computation (use tools).

---

## 9. Conversations and Memory

LLMs are stateless. A conversation is a growing message list your application re-sends each time. Cost grows linearly; context windows are finite.

**Managing long conversations**: sliding window (keep last N messages), summarization (periodically condense history), or hybrid (system prompt + running summary + recent messages).

### Four Types of "Memory"

These are often conflated, but they work differently:

1. **Parametric memory** — patterns stored in model weights (fixed after training)
2. **Working memory** — content in the current context window (temporary)
3. **Semantic memory** — documents or facts retrieved from external storage (persistent, queryable)
4. **Episodic memory** — records of past events, actions, and outcomes (persistent, experiential)

A vector database is not the same as an agent's action history. Each type needs different storage and retrieval strategies.

---

## 10. Temperature and Output Control

**Temperature** controls randomness. At 0: lowest randomness (nearly deterministic, but not guaranteed identical across runs). At 0.5–0.7: slight variation, good for general tasks. At 1.0+: more creative, more error-prone. **Top-p** limits sampling to the smallest token set reaching a cumulative probability threshold.

| Task | Temperature | Why |
|---|---|---|
| Data extraction, classification | 0 | Reproducible, exact |
| Code generation | 0–0.2 | Must be syntactically correct |
| Summarization, factual Q&A | 0–0.3 | Facts should not vary |
| Creative writing, brainstorming | 0.8–1.2 | Diversity is the goal |
| Evaluation | 0 | Must be reproducible |

Note: temperature 0 is *low-variance*, not an absolute determinism guarantee — infrastructure, floating-point behavior, and provider updates can still cause small differences.

---

## 11. Structured Outputs

Suppose an application asks an LLM to extract a customer's name, age, and subscription status. A normal text response might say: "The customer is Sarah, she is thirty-two and appears to have an active plan." A human understands this, but application code must guess where each value begins and ends. It may also receive `"32 years old"`, `"active customer"`, or malformed data on different calls.

**Structured outputs** solve this by constraining the response to a defined schema — an explicit contract requiring fields like `name`, `age`, and `is_active`, each with a defined type. Structured outputs can enforce schema adherence for successfully completed responses, but applications must still handle refusals, truncation, and semantically incorrect values.

Structured outputs make LLMs **composable** — output reliably feeds databases, functions, UIs, or other LLM calls.

A schema controls the **shape** of the answer, not its truth. The model may return a perfectly valid age of `320`. The structure is correct, but the value is not. Production code therefore needs two layers: schema validation (is it the right shape?) and domain validation (are the values plausible?).

---

## 12. Tool Calling

LLMs cannot access databases, run calculations, or send emails. **Tool calling** lets the model *request* that your code execute a function. Think of the model as a planner sitting behind a desk — it can decide that a calculator, database, or email service is needed, but it cannot operate those systems directly. Instead, it fills out a structured request describing which tool should be used and with which arguments. The surrounding application checks that request, executes the real function, and returns the result.

A concrete example: a user asks "What is the total price of three items costing €19.90 each?" The model requests `calculate(expression="3 * 19.90")`. The application validates the expression, executes the calculation, and returns `59.70`. The model then answers the user using that trusted result.

The **agentic loop** generalizes this: send messages + tool definitions → if the model returns `tool_calls`, execute them, append results, call again → repeat until the model returns `stop`.

The same mechanism becomes dangerous when the tool can modify data. A generated request like `refund_order(order_id=...)` is still only a model prediction — it may contain the wrong order number, exceed the user's permissions, or have been influenced by a malicious document. **The model is an untrusted caller.** Tool calls must be treated like untrusted API requests, not commands from an authority. Validate types, ranges, permissions, and authorization. For consequential write operations, require human confirmation.

**Tool design**: one clear purpose per tool, precise description (the model decides when to call based solely on it), strict input schema, bounded output, explicit error messages.

### From Tools to Protocols: MCP

Wiring tools in by hand works, but every application ends up re-implementing the same plumbing — describing each tool, passing arguments, returning results. The **Model Context Protocol (MCP)** is an open standard that turns this into a shared interface: tools, data sources, and whole services expose themselves as MCP "servers," and any MCP-aware application can discover and call them without custom glue. The trust model does not change — the model still only *requests*, and every request is still untrusted — but the connector is now standard and reusable instead of rewritten per project. You don't need it to begin; it is simply worth knowing that it exists, because by 2026 it is how much of the ecosystem connects models to the outside world.

---

## 13. Multimodal Capabilities

Modern LLMs process and generate images, audio, and video alongside text. **Vision** models receive images and reason about their content. **Whisper-style** models convert speech to text. **TTS** models generate speech. These combine into pipelines: audio → transcript → summary → structured output.

Each modality has specific failure modes: OCR misreads small text, vision models miss precise counts, transcription degrades with noise and accents, generated images fail on exact text rendering. Verify important information with modality-appropriate checks.

---

> **Part II checkpoint.** You should understand: statelessness and message roles; model selection trade-offs; system prompts and few-shot examples; the four types of memory; temperature control; structured outputs as composability; tool calling with the model as untrusted caller.

---

# Part III — RAG

*The document-assistant can be prompted well, but it still can't see files it was never trained on. This is the rung that hands it your data — RAG, the most important architecture pattern in LLM engineering: it solves knowledge cutoff and private-data access without retraining the model.*

---

## 14. Embeddings

An **embedding** is a vector (list of numbers) representing the meaning of text. Texts with similar meaning produce similar vectors, regardless of wording. "Revenue beat forecasts" and "Sales exceeded projections" share no words but have nearly identical embeddings.

**Cosine similarity** measures how aligned two embedding vectors are — imagine each as an arrow, and measure whether they point in the same direction. Score ranges from -1 (opposite) through 0 (unrelated) to 1 (identical meaning). Do not adopt universal thresholds like "0.8 = relevant" — calibrate on your actual data.

**Embedding models are not LLMs.** They are smaller, encoder-only Transformers (the "reader" variant from §5) that output a fixed-length vector instead of text. Fast, cheap, and can run locally. They are stored in **vector databases** (Chroma, Pinecone, Weaviate) optimized for nearest-neighbor search.

Important: embedding similarity indicates resemblance according to the model. It does not prove factual correctness, logical equivalence, or user authorization. "Terminate employment" and "do not terminate employment" may be close in embedding space despite opposite meaning.

---

## 15. The RAG Pattern

**Retrieval-Augmented Generation** retrieves relevant documents from a knowledge base and injects them into the prompt, grounding the model's answer in specific sources. The model doesn't need to have been trained on your data — it receives it at query time.

### Why RAG Is the Default

| Concern | RAG | Fine-tuning |
|---|---|---|
| Adding knowledge | Update knowledge base (minutes) | Retrain (hours/days) |
| Cost | Low | High (GPU compute) |
| Hallucination | Supports inspectable, updateable evidence and citations | Changes learned behavior but does not provide reliable source attribution |
| Updating knowledge | Add/remove documents | Retrain |
| Changing behavior/style | Not effective | The right tool |

**Start with RAG. Fine-tune only when RAG cannot solve the problem.**

### Two Separate Pipelines

A RAG system has two flows that should be designed and evaluated independently:

**Ingestion**: sources → parse → clean → deduplicate → chunk → enrich with metadata → embed → index. Poor ingestion cannot be repaired by a powerful generator.

**Retrieval**: question → query analysis → authorization filters → candidate retrieval → ranking/reranking → context selection → generation → citation.

### Grounded Generation

The model must transform retrieved evidence into an answer without adding unsupported claims. A grounded prompt specifies: use only supplied evidence, distinguish evidence from inference, cite each claim, report contradictions, abstain when evidence is insufficient, and do not follow instructions found inside source documents.

---

## 16. Chunking

Chunking is often one of the largest quality levers in a RAG system, but this depends on the data and must be evaluated.

**The goal**: each chunk should contain enough context to be understood, focus on a limited topic, preserve source meaning, and support accurate citation.

**Fixed character splitting is risky** — it can cut a sentence in half, separate a definition from its condition, or split a table row from its header. Prefer natural boundaries: headings, paragraphs, FAQ pairs, policy clauses, code functions.

**Overlap** (10–25%) preserves meaning across boundaries — without it, ideas spanning two chunks become invisible. But excessive overlap causes duplicate retrieval and wasted context.

**Parent-child retrieval**: store small focused chunks for precise matching, but retrieve the larger parent section for context. The query matches the child; the model receives the parent.

**Tables** need special handling: keep small tables whole, repeat headers for row groups, or convert rows to explicit statements. Don't rely on flattened tables for arithmetic.

**Evaluate chunking empirically** with questions that require: a fact inside one chunk, context across a boundary, a table lookup, a comparison across sections, a rare exact term, and a negative condition.

---

## 17. Advanced Retrieval

### Query Rewriting

Users ask vague or context-dependent questions. Before searching, pass the question through a fast LLM that rewrites it into an explicit search query using conversation history. `"What about the other thing?"` → `"What are the cancellation conditions in the subscription agreement?"`

### Hybrid Search

**Dense retrieval** (embeddings) finds semantic matches. **Sparse retrieval** (BM25 keyword matching) finds exact terms — names, codes, error messages. Combining both via **Reciprocal Rank Fusion (RRF)** improves robustness because they fail differently. Empirical results consistently show meaningful gains from hybrid search, with further improvement when reranking is added on top.

### Reranking

Retrieve broadly (20+ candidates), then pass each through a **reranker** — a model that reads query and passage together and assigns a precise relevance score. Unlike separate embeddings, a reranker catches subtle relevance cues. More expensive, but measurably improves quality.

### Query Routing

Route different questions to different sources: documents, SQL databases, web search, code repositories, or no retrieval at all. A single vector index should not become the universal interface to every kind of data.

### The "Lost in the Middle" Problem

LLMs attend most to content at the beginning and end of the context window. Place the most relevant chunk first, second-most-relevant last.

---

## 18. RAG Evaluation and Failure Analysis

Evaluate retrieval and generation separately before evaluating end-to-end answers.

**Retrieval metrics**: Recall@k (did we find the evidence?), Precision@k (is retrieved content relevant?), MRR (how high is the first relevant result?), NDCG (ranking quality).

**Generation metrics**: faithfulness to evidence, citation correctness (does the cited source actually support the claim?), citation completeness (are all claims supported?), answer relevance, appropriate abstention.

### Failure Diagnosis

A wrong answer flows through a pipeline — identify the stage:

| Failure | Likely cause | Mitigation |
|---|---|---|
| Relevant source absent | Coverage gap | Add sources |
| Source exists but not indexed | Ingestion bug | Fix parsing/refresh |
| Exact identifier missed | Dense-only search | Add sparse/structured search |
| Wrong passage ranked high | Embedding imprecision | Rerank, add metadata filters |
| Answer spans chunk boundary | Bad chunking | Overlap, parent retrieval |
| Model ignores correct chunk | Context overload | Reduce context, improve ordering |
| Model invents unsupported detail | Generation hallucination | Stronger grounding, verification pass |
| Unauthorized content retrieved | Missing ACL | Enforce permissions before retrieval |

---

> **Part III checkpoint.** You should understand: embeddings and cosine similarity; the two RAG pipelines (ingestion and retrieval); why chunking strategy matters; query rewriting, hybrid search, and reranking; grounded generation; and how to diagnose whether a failure is in retrieval or generation.

---

# Part IV — Fine-Tuning

*Retrieval gave the assistant your facts; it may still miss your tone, your formats, your domain reflexes. This rung changes how the model behaves — not what it knows.*

---

## 19. When to Fine-Tune

Fine-tuning changes **behavior** — output style, format, domain terminology, task-specific patterns. It does not reliably add factual **knowledge** (use RAG) or real-time data (use tools).

Before fine-tuning, ask: Is the information absent? (→ retrieval). Is the instruction ambiguous? (→ better prompt). Is the output format failing? (→ structured output). Is the task deterministic? (→ code). Is the base model simply incapable with good context? (→ stronger model, then consider fine-tuning). Do you have enough high-quality training data?

### What Fine-Tuning Actually Does

It is a miniature Phase 2 (SFT): you provide (input, desired output) pairs, and parameters adjust to make those outputs more likely. Most pre-trained capabilities are often retained, but fine-tuning can also cause regressions or **catastrophic forgetting** — degrading previously learned abilities — which must be evaluated. The model generalizes from examples, not memorizes them.

---

## 20. Fine-Tuning Methods

Not all model adaptation solves the same problem. Before choosing a method, ask what must change: the model's response pattern, its familiarity with a domain, its preference between acceptable answers, or its size and cost.

**Supervised fine-tuning (SFT)** teaches by demonstration: "When you receive an input like this, produce an output like that." Use for repeated task patterns, domain style, tool-use conventions. SFT imitates its training targets — inconsistent, verbose, or wrong examples teach those properties.

**Continued pre-training** teaches through exposure: "Become more familiar with the language and patterns of this domain." Exposes a model to more domain text using the language-model objective. Improves domain vocabulary and familiarity but requires more data and compute.

**Preference optimization** (DPO, RLHF) teaches comparison: "Between these two plausible answers, prefer this one." Uses paired preferred/rejected responses. Useful when quality is easier to compare than to write perfectly.

**Distillation** teaches imitation: "Learn to reproduce the useful behavior of a larger model using a smaller one." Trains a student model on teacher outputs. Lower cost and latency, but inherits teacher errors.

These methods can complement each other. For a legal assistant, continued pre-training may improve familiarity with legal vocabulary; SFT may teach the required memorandum format; preference optimization may favor cautious, well-supported answers over confident speculation; distillation may transfer the final behavior into a cheaper model. Each step introduces additional cost and evaluation requirements.

### Data Quality Matters Most

Define target behavior before collecting data. Include edge cases, negative examples (insufficient evidence, out-of-scope requests), and abstention examples. A dataset of only clean answerable examples trains overconfidence. Split by meaningful groups (not random rows) to prevent data leakage.

### Overfitting

Training loss decreasing while validation loss increases = overfitting. Prevention: validation set, fewer epochs (one is often enough for large datasets), early stopping.

### The Cost Argument

A fine-tuned cheap model often beats an expensive general model on a specific task. A relatively small training investment amortizes across every subsequent call. Compare: base model with best prompt, base model with RAG, fine-tuned model, and a stronger reference model.

---

## 21. QLoRA — Fine-Tuning on Consumer Hardware

Full fine-tuning of a 65B model requires ~780 GB GPU memory (model + gradients + optimizer states). **QLoRA** makes it possible on a single consumer GPU by combining two techniques:

**LoRA** (Low-Rank Adaptation) freezes the entire pre-trained model and inserts small trainable adapters alongside specific layers. Only these adapters are updated — less than 1% of parameters. The intuition: the change needed for a new task lives in a low-dimensional subspace. A few million strategically placed parameters are enough.

**4-bit quantization** compresses model weights from 16-bit to 4-bit using **NF4** (Normal Float 4), a format optimized for the normal distribution that neural network weights follow. Reduces memory ~4×. **Double quantization** compresses the quantization constants themselves.

| Setup | GPU Memory |
|---|---|
| Full fine-tuning 65B | ~780 GB |
| QLoRA 65B | ~48 GB |
| QLoRA 3B | ~8 GB (fits a free cloud GPU) |

After training, adapters can be merged into the base model for zero-overhead inference, or kept separate for easy swapping between variants.

---

> **Part IV checkpoint.** Fine-tuning changes behavior, not knowledge. LoRA trains small adapters while freezing the base model. Quantization compresses weights to fit consumer GPUs. Data quality matters more than optimization settings. Overfitting is the primary risk.

---

# Part V — Agents

*So far the assistant answers. This rung lets it act — choosing tools in a loop to reach a goal — while continually asking whether that autonomy is worth its risks.*

---

## 22. Workflows vs Agents

A **workflow** follows a predefined sequence — application code controls the path. The model performs steps, but engineers decide the order. An **agent** is given a goal and dynamically decides what step to take next.

**Default to workflows** when steps are known, compliance requires predictability, actions are consequential, or cost must be bounded. Use agents when the path cannot be known in advance, tool choice depends on intermediate discoveries, or the environment requires exploration.

**Autonomy is a spectrum:**
```
LLM answers → recommends action → selects read-only tools → prepares write for approval → executes bounded actions → executes open-ended actions
```
Move right only when evaluation, controls, and business value justify the risk. Many "agent" applications are more reliable as workflows with one or two bounded decision points.

---

## 23. Agent Architecture

Three ingredients: a **goal** (system prompt), **tools** (functions it can request), and a **loop** (code feeding results back until the model decides the task is complete).

### The ReAct Pattern

Most agents alternate thinking and acting:
```
Thought: I need to find the current price.
Action:  search_product("wireless headphones")
Observation: $79.99 retail, $64.99 on sale
Thought: 19% below retail. Check seller rating.
Action:  check_seller_rating(seller_id="...")
Observation: 98.5% positive
Thought: Genuine deal. Notify user.
Action:  notify("Found headphones at $64.99...")
```

### Design Principles

**Least privilege** — only the tools needed. **Bounded loops** — maximum iterations; "continue until done" is not safe. **Structured state** — don't force the model to reconstruct critical data from a long transcript; store fields like `completed_steps`, `remaining_budget`, `current_status`. **Observable actions** — log every tool call. **Deterministic** — temperature 0 for consequential decisions.

**Recovery**: agents may retry after timeouts without knowing if an action succeeded. Use idempotency keys, transaction IDs, and status checks. Never allow "retry payment" to create duplicates.

---

## 24. Multi-Agent Systems

Large tool sets can make tool selection harder. Specializing agents with 2–3 focused tools each often improves quality, but this should be confirmed by evaluation, not assumed. Benefits: narrower prompts, parallel execution, different models per task, independent verification.

Costs: token multiplication, coordination errors, cascading hallucinations, wider security surface, and **false confidence from agreement** — agents sharing the same model, prompt, or data may agree on the same wrong answer.

Common patterns: **router** (directs to specialists), **planner-executor** (one decomposes, another performs), **generator-critic** (one drafts, another checks), **parallel workers** (independent subtasks), **supervisor hierarchy** (controller delegates and merges).

Use multi-agent only when subtasks are genuinely separable. Do not replace one clear prompt with five agents for architectural novelty.

---

> **Part V checkpoint.** You should understand: workflows vs agents and when to use each; the bounded agent loop; structured state; ReAct; multi-agent trade-offs; idempotency; and safe autonomy controls.

---

# Part VI — Production

*A capable prototype is not a product. This last rung is everything in between: knowing whether it works (evaluation), what it costs, and how it fails under attack (security).*

---

## 25. Evaluation

Without systematic evaluation, every change — prompt tweak, model swap, chunking strategy — might improve one case and break five others.

**Build the eval set before optimizing.** Include common cases, edge cases, known failures, no-answer cases, adversarial inputs, and different languages. Start with 20–50 carefully selected cases, then expand according to risk, usage diversity, and observed production failures.

**Deterministic metrics when possible**: exact match, schema validity, unit tests, citation span match, numerical tolerance. For classification: precision, recall, F1 (accuracy can be misleading on imbalanced data). For numerical predictions: MAE, RMSE.

**LLM-as-Judge** for subjective quality (coherence, helpfulness). The judge receives the question, answer, and source evidence, then produces a structured score. Use temperature 0. Judge limitations: position bias, verbosity bias, self-preference, sensitivity to rubric wording. A judge score is another model output, not objective truth. Calibrate against human-labeled examples.

**Average scores hide risk.** Report slices by category, language, difficulty, and sensitivity. A 95% average can hide a 40% failure rate on the most important category.

**Observability**: log every LLM call (model, tokens, cost, latency, success). Trace multi-step pipelines. Monitor for drift — inputs, output length, retrieval patterns, refusal rates, costs. Build from the start; retrofitting is much harder.

---

## 26. Cost Thinking

You pay per token: input + output. Output tokens typically cost several times more than input (sequential generation is compute-intensive). Individual calls are cheap — fractions of a cent — but at scale, costs compound quickly.

**Use the cheapest model that works.** Test on the expensive model, deploy on the cheap one. **Prompt caching** gives significant discounts on repeated prefixes (varies by provider). **Shorter prompts** save money at scale. **Fine-tune for cost reduction** — a small training investment producing a specialized cheap model that matches a frontier model on your task can reduce per-call cost dramatically. **Batch APIs** are typically cheaper for non-interactive workloads.

**Monitor cost per successful task**, not just cost per call. An agent that loops 15 times to produce a wrong answer is infinitely more expensive than one that gets it right in 3 steps.

---

## 27. Security

### Prompt Injection

The #1 LLM security risk (OWASP Top 10). Untrusted content — user messages, retrieved documents, scraped pages — can attempt to override the system prompt. **Direct injection** comes from the user. **Indirect injection** is hidden in documents the model retrieves — in agentic systems with tool access, this can trigger real-world actions.

No prompt wording can guarantee immunity. The strongest controls are permissions, tool validation, isolation, approval gates, and monitoring. Supplementary measures include: structural separation (system role for instructions, user role for data); labeling untrusted content explicitly; least-privilege tools; validating tool arguments. Input filtering (detecting instruction-like patterns) is only a weak secondary defense — attackers can phrase injections indirectly, and legitimate documents can contain instructional language.

### Excessive Agency

A model with unnecessary tools will eventually misuse them. Minimize tool count and scope. Separate read and write permissions. Require confirmation for consequential actions. Cap cost, time, and steps.

### Data Poisoning

In RAG systems, the knowledge base is a trust boundary. Restrict write access, validate content before ingestion, audit retrieval patterns. Treat it like a database, not a shared folder.

**Model output is untrusted input to downstream systems.** Never directly execute generated SQL, shell commands, HTML, or file paths. Parse, validate, authorize, escape, and sandbox it.

---

## 28. Architecture Decision Guide

*The whole arc, reassembled into one decision procedure: work out what a system actually needs, then add only the machinery that need requires — in order, and stop as soon as it works.*

### Step 1: Is an LLM necessary?

Use deterministic software for exact rules, arithmetic, known queries, strict validation. Use an LLM when flexible language interpretation or generation adds value.

### Step 2: What information is needed?

| Type | Best source |
|---|---|
| General linguistic patterns | Model weights |
| Private or sourceable documents | RAG |
| Exact structured values | Database/API tool |
| Current public information | Search tool |
| User/session state | Application storage |

### Step 3: How much freedom?

Known steps → workflow. Limited dynamic choice → workflow with routing. Open-ended exploration → bounded agent. Consequential actions → approval gates.

### Step 4: Simplest baseline first

```
1. One good prompt
2. Structured output and validation
3. Add tools for exact/current data
4. Add RAG for documents
5. Improve retrieval and evaluation
6. Route across models if justified
7. Fine-tune if repeated behavior still fails
8. Add bounded agents only for dynamic workflows
9. Multi-agent only when measured value exists
```

### Step 5: What can go wrong?

For each stage: likely failure, detection signal, safe fallback, owner, recovery action.

---

> **Part VI checkpoint.** You should understand: evaluation before optimization; deterministic vs LLM-judge metrics; cost per successful task; prompt injection and data poisoning mitigations; and the progressive architecture from simple prompt to multi-agent system.

---

## Glossary

| Term | Definition |
|---|---|
| **Neural network** | Program made of layers of mathematical operations that learns patterns from data |
| **LLM** | Large Language Model — a neural network trained to predict and generate text |
| **Parameter** | A numerical weight inside the model, adjusted during training |
| **Token** | Sub-word unit processed by a language model |
| **Vector** | An ordered list of numbers |
| **Probability distribution** | Values assigned to all possible outcomes that sum to 1 |
| **Autoregressive** | Generating one token at a time, each conditioned on all prior tokens |
| **Hallucination** | Confident but false, fabricated, or unsupported model output |
| **Pre-training** | Broad training on massive text via next-token prediction |
| **SFT** | Supervised Fine-Tuning on (instruction, response) pairs |
| **RLHF** | Reinforcement Learning from Human Feedback |
| **DPO** | Direct Preference Optimization — simpler alternative to RLHF |
| **Base model** | Pre-trained, not yet instruction-tuned |
| **Instruct model** | Post-trained to follow instructions |
| **BPE** | Byte-Pair Encoding — dominant tokenization algorithm |
| **Context window** | Maximum tokens a model can process in one call |
| **Gradient** | Correction signal indicating how to adjust parameters to reduce errors |
| **Transformer** | Neural architecture underlying all modern LLMs |
| **Self-attention** | Mechanism letting each token attend to every permitted earlier token |
| **Dot product** | Multiply corresponding numbers in two vectors, sum the results |
| **Softmax** | Converts any list of numbers into a probability distribution |
| **Multi-head attention** | Multiple parallel attention computations for different relationship types |
| **FFN** | Feed-Forward Network — per-token transformation; helps store learned associations (knowledge is distributed, not localized) |
| **Residual connection** | Adds a layer's input to its output, preventing gradient vanishing |
| **Causal masking** | Blocking future token positions during generation |
| **Encoder** | Reads all tokens bidirectionally (the "reader") |
| **Decoder** | Generates tokens sequentially with masking (the "writer") |
| **Stateless** | Each API call is independent; no memory between calls |
| **System prompt** | Message setting model behavior for the conversation |
| **Zero-shot** | Task with no examples |
| **Few-shot** | Task with demonstration examples |
| **Chain-of-Thought** | Asking the model to show reasoning steps |
| **Prompt chaining** | Sequential focused LLM calls |
| **Context engineering** | Selecting and structuring all information supplied to a model |
| **Temperature** | Controls randomness; 0 = lowest randomness, but not a guarantee of identical outputs |
| **Top-p** | Sampling from the smallest token set reaching a cumulative probability |
| **Structured output** | Response constrained to a defined schema |
| **Tool calling** | Model requests code execution; never executes directly |
| **MCP** | Model Context Protocol — open standard connecting models to tools and data sources |
| **Embedding** | Vector representing the meaning of text |
| **Cosine similarity** | Measures directional alignment between two vectors |
| **Vector database** | Storage optimized for similarity search |
| **RAG** | Retrieval-Augmented Generation — injecting retrieved docs into the prompt |
| **Grounding** | Anchoring answers in specific source material |
| **Chunking** | Splitting documents into retrievable units |
| **BM25** | Classic keyword-matching algorithm |
| **Hybrid search** | Combining embedding-based and keyword-based retrieval |
| **RRF** | Reciprocal Rank Fusion — merging ranked lists from different retrievers |
| **Reranker** | Model scoring query-passage relevance jointly |
| **Fine-tuning** | Continuing training to change model behavior |
| **Overfitting** | Memorizing training data instead of generalizing |
| **Epoch** | One complete pass through training data |
| **LoRA** | Low-Rank Adaptation — small trainable adapters on a frozen model |
| **QLoRA** | LoRA on a 4-bit quantized base model |
| **Quantization** | Compressing weights to fewer bits |
| **NF4** | Normal Float 4 — quantization format optimized for neural network weights |
| **Distillation** | Training a smaller model from a stronger teacher's outputs |
| **Workflow** | Predefined sequence of steps; code controls the path |
| **Agent** | LLM dynamically choosing actions in a loop toward a goal |
| **ReAct** | Reason + Act — alternating thinking and tool use |
| **Idempotency** | Repeating an operation does not create additional effects |
| **LLM-as-Judge** | Using one model to evaluate another's output |
| **Precision** | Among predicted positives, fraction truly positive |
| **Recall** | Among true positives, fraction found |
| **RMSE** | Root mean squared error — penalizes large errors |
| **Prompt injection** | Untrusted content attempting to alter model behavior |
| **Data poisoning** | Malicious documents corrupting a knowledge base |
| **Observability** | Traces, metrics, and logs revealing system behavior |

---

## Revision Questions

**Foundations**: Why does next-token prediction produce both useful generalization and hallucinations? What is the difference between context and persistent memory? Why is generation sequential even though input is processed in parallel?

**Working with models**: Why should untrusted documents be separated from trusted instructions? Why does schema-valid output still need semantic validation? Why must tool arguments be validated outside the model? What are the four types of "memory"?

**RAG**: When should data come from RAG vs a database tool vs model weights? Why is embedding similarity not the same as truth? How do dense and sparse search fail differently? Why is there no universal chunk size? How do you diagnose whether a wrong answer came from retrieval or generation?

**Fine-tuning**: When is fine-tuning justified vs prompting or RAG? Why are negative and abstention examples important? How do LoRA and QLoRA reduce training memory? What regressions should be checked after fine-tuning?

**Agents and production**: When should a workflow be preferred over an agent? What limits must bound an agent loop? Why doesn't agreement between agents guarantee correctness? What biases affect LLM judges? Why can't prompt injection be solved by a stronger system prompt alone?

---

## References

1. Vaswani et al., *Attention Is All You Need* — arxiv.org/abs/1706.03762
2. Hoffmann et al., *Training Compute-Optimal Large Language Models* — arxiv.org/abs/2203.15556
3. Lewis et al., *Retrieval-Augmented Generation* — arxiv.org/abs/2005.11401
4. Liu et al., *Lost in the Middle* — arxiv.org/abs/2307.03172
5. Hu et al., *LoRA* — arxiv.org/abs/2106.09685
6. Dettmers et al., *QLoRA* — arxiv.org/abs/2305.14314
7. Rafailov et al., *Direct Preference Optimization* — arxiv.org/abs/2305.18290
8. Zheng et al., *Judging LLM-as-a-Judge* — arxiv.org/abs/2306.05685
9. OWASP, *Top 10 for LLM Applications* — genai.owasp.org/llm-top-10/
