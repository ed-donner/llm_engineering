# RAG (Retrieval Augmented Generation) — Complete Notes
> Written for future reference. If you're reading this after a long break, start from Page 1 and the concepts will come back fast.

---

## Page 1 — What & Why RAG Exists

### The Problem LLMs Have

LLMs like GPT are trained on internet data up to a certain date. They have two critical limitations:

1. **No private data** — The LLM has never seen your company's documents, your codebase, your internal policies.
2. **Context limit** — You cannot dump 1000 pages into a single prompt. Every LLM has a token limit.

So if you ask GPT "Who is Averi Lancaster at Insurellm?" — it will either say it doesn't know, or worse, **hallucinate** a confident but wrong answer.

### The RAG Solution

Instead of giving the LLM everything, RAG finds only the **relevant pieces** at query time and feeds just those to the LLM.

**The Open-Book Exam Analogy:**
- LLM = the student
- Your documents = the textbook
- RAG = the system that finds the right page before the exam question

### Without RAG vs With RAG

| | Without RAG | With RAG |
|---|---|---|
| Knowledge source | Only training data | Your documents |
| Private data | ❌ | ✅ |
| Accuracy | Hallucination risk | Grounded in real docs |
| Up-to-date info | ❌ cutoff date | ✅ whatever you feed |

---

## Page 2 — Core Concepts (The Vocabulary)

### Embedding
Text converted into a list of numbers that captures **meaning**. Similar meaning = similar numbers.

Example:
```
"Who is Averi?"    → [0.23, -0.11, 0.87, ...]
"Tell me about Averi" → [0.21, -0.09, 0.85, ...]   ← very similar!
"Pizza recipe"     → [-0.55, 0.72, -0.34, ...]   ← very different
```

### Vector
The list of numbers produced by an embedding. Each chunk of text becomes one vector.
- HuggingFace all-MiniLM-L6-v2 → 384 numbers per text
- OpenAI text-embedding-3-large → 3072 numbers per text

### Vector Store / Chroma
A database designed to store vectors and search them by **meaning similarity** — not exact keyword match. Chroma stores them on disk so you compute once and reuse forever.

### Cosine Similarity
How the vector store finds relevant chunks. It measures the angle between two vectors. Smaller angle = more similar meaning. This is what powers semantic search.

### Chunk
A small piece of a document (~500–1000 characters). Documents are split because:
1. LLMs have context limits
2. Smaller pieces = more precise retrieval
3. You only want the relevant parts, not entire documents

### Chunk Overlap
Each chunk shares some characters with the next one. If a sentence sits at the boundary between two chunks, it won't be lost.

```
Chunk 1: [============================|----]
Chunk 2:                         [----========================]
                                  ↑ overlap (200 chars)
```

### Retriever
The component that takes a question, embeds it, searches Chroma, and returns the top-k most similar chunks.

### Temperature
Controls LLM randomness.
- `0` = always pick the highest probability token → factual, consistent, deterministic
- `1` = tokens are sampled by probability → more varied, creative
- For Q&A systems: always use `temperature=0`

### k (RETRIEVAL_K)
How many chunks the retriever returns. Default is 4. The course used 10 for richer context.

### t-SNE
Algorithm to compress 384-dimensional vectors down to 2D or 3D for human visualization. Used in Day 2 to see clusters of similar document types.

### LangChain
A framework (like Express.js for Node) that provides pre-built components for every step of RAG — loading, chunking, embedding, storing, retrieving, and chaining to LLMs — so you don't write everything from scratch.

---

## Page 3 — The Full RAG Architecture

### Phase 1: Indexing (Run Once)
```
.md / .pdf / .txt files on disk
        ↓   DirectoryLoader + TextLoader
LangChain Documents (with metadata: doc_type, filename)
        ↓   RecursiveCharacterTextSplitter (chunk_size=500, overlap=200)
Chunks (small pieces of text)
        ↓   HuggingFaceEmbeddings OR OpenAIEmbeddings
Vectors (list of numbers per chunk)
        ↓   Chroma.from_documents()
vector_db/ saved on disk  ✓ (permanent, reusable)
```

### Phase 2: Querying (Every user question)
```
User Question
        ↓   combined_question() — merge with chat history
Combined Question String
        ↓   retriever.invoke() — embeds question, cosine similarity search
Top-k Chunks from Chroma
        ↓   "\n\n".join(doc.page_content for doc in docs)
Context String
        ↓   SYSTEM_PROMPT.format(context=context)
System Prompt with Context Injected
        ↓   llm.invoke([SystemMessage + History + HumanMessage])
Answer + Source Documents returned
```

### Critical Rule
**The same embedding model MUST be used in both phases.**
If you embed documents with MiniLM but search with OpenAI embeddings, the numbers are incompatible and results will be garbage.

---

## Page 4 — Code Explained Line by Line

### answer.py — Build the Vector DB (Run Once)

```python
DB_NAME = str(Path(__file__).parent.parent / "vector_db")
KNOWLEDGE_BASE = str(Path(__file__).parent.parent / "knowledge-base")
```
`__file__` = current file's location on disk
`.parent.parent` = go two folders up
`/ "vector_db"` = append folder name to path

So if answer.py is at: `projects/llm/src/answer.py`
Then DB_NAME = `projects/llm/vector_db`

---

```python
def fetch_documents():
    folders = glob.glob(str(Path(KNOWLEDGE_BASE) / "*"))
    documents = []
    for folder in folders:
        doc_type = os.path.basename(folder)   # "products", "employees", etc.
        loader = DirectoryLoader(folder, glob="**/*.md", loader_cls=TextLoader, ...)
        folder_docs = loader.load()
        for doc in folder_docs:
            doc.metadata["doc_type"] = doc_type   # tag each doc
            documents.append(doc)
    return documents
```
Scans every subfolder in knowledge-base. Tags each document with which folder it came from (doc_type). This metadata helps later if you want to filter results by category.

---

```python
def create_chunks(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    return chunks
```
Splits every document into 500-character pieces with 200-character overlap. Metadata from the original document is preserved in each chunk automatically.

Why `RecursiveCharacterTextSplitter`? It tries to split on natural boundaries first — paragraphs, then sentences, then words — rather than just cutting at character 500 blindly.

---

```python
def create_embeddings(chunks):
    if os.path.exists(DB_NAME):
        Chroma(persist_directory=DB_NAME, embedding_function=embeddings).delete_collection()

    vectorstore = Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=DB_NAME
    )
```
Deletes old DB if it exists (fresh rebuild). Then embeds every chunk and stores in Chroma. `persist_directory` means it saves to disk — not just in memory.

---

```python
if __name__ == "__main__":
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion complete")
```
This block only runs when you execute `python answer.py` directly. If another file imports from answer.py, this block is skipped. Standard Python pattern.

---

### ingest.py — Answer Questions with RAG

```python
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vectorstore = Chroma(persist_directory=DB_NAME, embedding_function=embeddings)
retriever = vectorstore.as_retriever()
llm = ChatOpenAI(temperature=0, model_name=MODEL)
```
Reconnects to the existing vector DB on disk. No rebuilding. Creates retriever and LLM objects. These two are the heart of RAG.

- `retriever` = handles searching Chroma
- `llm` = handles generating the answer

---

```python
SYSTEM_PROMPT = """
You are a knowledgeable assistant representing Insurellm.
If relevant, use the given context to answer any question.
If you don't know the answer, say so.
Context:
{context}
"""
```
Three smart design choices:
1. "If relevant" = LLM has flexibility for general questions
2. "If you don't know, say so" = reduces hallucination
3. `{context}` = placeholder where retrieved chunks will be injected

---

```python
def combined_question(question: str, history: list[dict] = []) -> str:
    prior = "\n".join(m["content"] for m in history if m["role"] == "user")
    return prior + "\n" + question
```
**Why this exists:** Suppose the conversation is:
```
User: "Who is Averi Lancaster?"
Bot:  "She is a senior engineer..."
User: "What is her salary?"
```
The word "her" means nothing to the retriever without context. This function combines all prior user messages + current question before searching Chroma, so the retriever understands "her" = Averi Lancaster.

---

```python
def answer_question(question: str, history: list[dict] = []) -> tuple[str, list[Document]]:
    combined = combined_question(question, history)   # Step 1: Context-aware question
    docs = fetch_context(combined)                     # Step 2: Search Chroma
    context = "\n\n".join(doc.page_content for doc in docs)  # Step 3: Format chunks
    system_prompt = SYSTEM_PROMPT.format(context=context)     # Step 4: Inject context
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(convert_to_messages(history))              # Step 5: Add chat history
    messages.append(HumanMessage(content=question))
    response = llm.invoke(messages)                            # Step 6: Generate answer
    return response.content, docs                              # Step 7: Return answer + sources
```
This is the complete RAG pipeline in one function. Every step matters.

---

## Page 5 — Notebook vs Production Code Comparison

| Feature | Day 3 Notebook | Production (ingest.py) |
|---|---|---|
| Conversation memory to LLM | ❌ history ignored | ✅ full history passed |
| Context-aware retrieval | ❌ single question only | ✅ combined with history |
| Chunks retrieved | 4 (default) | 10 (RETRIEVAL_K) |
| Source documents returned | ❌ | ✅ enables citations |
| Code organization | 1 notebook | 3 separate files |
| Embeddings | HuggingFace (free) | OpenAI (better quality) |

### File Role Summary
| File | Role | When to run |
|---|---|---|
| `answer.py` | Builds vector DB from documents | Once, or when docs change |
| `ingest.py` | RAG logic — retrieval + generation | Called on every user question |
| `notebook / app` | UI layer (Gradio) | Entry point for users |

---

## Page 6 — Embedding Model Choices

| Model | Provider | Dimensions | Cost | Quality |
|---|---|---|---|---|
| all-MiniLM-L6-v2 | HuggingFace | 384 | Free, local | Good |
| text-embedding-3-small | OpenAI | 1536 | Cheap | Better |
| text-embedding-3-large | OpenAI | 3072 | Moderate | Best |

**Rule:** Use the same model for indexing AND querying. Never mix.

---

## Page 7 — LangChain Components Quick Reference

| Component | Import | What it does |
|---|---|---|
| `DirectoryLoader` | `langchain_community.document_loaders` | Load all files from folder |
| `TextLoader` | `langchain_community.document_loaders` | Read files as plain text |
| `RecursiveCharacterTextSplitter` | `langchain_text_splitters` | Split into chunks |
| `HuggingFaceEmbeddings` | `langchain_huggingface` | Free local embeddings |
| `OpenAIEmbeddings` | `langchain_openai` | OpenAI embeddings |
| `Chroma` | `langchain_chroma` | Vector database |
| `vectorstore.as_retriever()` | — | Create retriever from Chroma |
| `ChatOpenAI` | `langchain_openai` | OpenAI LLM |
| `ChatOllama` | `langchain_ollama` | Local LLM via Ollama |
| `SystemMessage` | `langchain_core.messages` | System prompt message |
| `HumanMessage` | `langchain_core.messages` | User message |
| `convert_to_messages(history)` | `langchain_core.messages` | Convert history dict to LangChain messages |

---

## Page 8 — What's Missing (Future Improvements)

The course code is good but has these gaps — future days likely cover them:

### 1. No Source Citations in UI
The code returns `docs` alongside the answer but the Gradio UI doesn't show them. A production app should show "Answer based on: employees/averi.md"

### 2. No Reranking
After retrieving top-10 chunks, they're all treated equally. In production you'd add a **reranker** (like Cohere Rerank) that scores which chunks are truly most relevant.

### 3. No Metadata Filtering
The retriever searches all documents. You could filter: "only search in the contracts/ folder" using Chroma's `where` parameter.

### 4. No Streaming
The LLM waits until the full answer is ready. Production apps stream token by token so users see text appearing in real time.

### 5. No Evaluation
How do you know if RAG is working well? You'd add RAGAS or similar evaluation framework to measure retrieval quality and answer accuracy.

---

## Page 9 — When to Use RAG in Your Projects

Use RAG when you have:
- **Private documents** the LLM doesn't know about (internal docs, codebases, PDFs)
- **Large knowledge bases** too big to fit in a single prompt
- **Frequently updated data** where you don't want to retrain a model
- **Need for citations** — you want to show which document the answer came from

Don't use RAG when:
- Your knowledge base is small enough to fit in the context window (just use system prompt)
- You need real-time data (use web search / APIs instead)
- The LLM already knows the answer well from training

---

## Page 10 — Cheat Sheet (Read This First After Long Break)

### One-Line Summary
> Embed docs → store vectors in Chroma → embed question → find similar vectors → give chunks to LLM as context → get grounded answer

### Critical Rules
1. **Same embedding model** for indexing AND querying — non-negotiable
2. **Chunk before embedding** — never embed whole documents
3. **temperature=0** for factual Q&A
4. **Run ingestion once**, reuse the DB forever (until docs change)
5. **Combine history + question** before retrieval for multi-turn chats

### The 7-Step RAG Pipeline
```
1. combined_question()     → merge history + question
2. retriever.invoke()      → embed question, search Chroma
3. join chunks             → format context string
4. SYSTEM_PROMPT.format()  → inject context into prompt
5. build messages[]        → SystemMessage + history + HumanMessage
6. llm.invoke()            → generate answer
7. return answer + docs    → response and source documents
```

### Quick Troubleshooting
| Problem | Likely Cause |
|---|---|
| Retriever returns irrelevant chunks | Wrong embedding model, or chunks too large |
| LLM ignores context | System prompt not instructing to use it |
| Multi-turn context breaks | Not combining history before retrieval |
| ImportError in LangChain | Version mismatch — upgrade all together |
| Empty retrieval results | DB built with different embedding model |