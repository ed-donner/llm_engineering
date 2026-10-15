"""
Wires to real RAG stack (src/intelligence_v3.py) into the rag_eval
framework and runs the full evaluation dataset through it.

Run from the REPO ROOT (same level as src/ and rag_eval/):
    python run_real_eval.py
"""
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from src.intelligence_v3 import (
    Conversation,
    ChromaRetriever,
    create_provider,
    format_context,
    RAG_PROMPT_TEMPLATE,
    user,
)
from rag_eval import (
    RagResult,
    RetrievedChunk as EvalChunk,   # aliased -- distinct from intelligence_v3's RetrievedChunk
    run_evaluation,
    save_results_csv,
    report,
)

# ----  Real config ----
CHROMA_PATH = "./chroma_db"   # relative to repo root -- see note below
COLLECTION_NAME = "gemma_local2"

vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=OllamaEmbeddings(model="mxbai-embed-large"),
    persist_directory=CHROMA_PATH,
)
retriever = ChromaRetriever(vectorstore, default_k=5)
# rag_provider = create_provider("gemma-4-31b-it")
rag_provider = create_provider("gpt-5.4-nano")
SYSTEM_PROMPT = "Answer questions using only the provided context."


def my_rag_pipeline(question: str) -> RagResult:
    """
    Mirrors Intelligence.ask()'s RAG branch exactly (same retriever, same
    prompt template, same provider call) but:
      - retrieves only ONCE, so we can score retrieval quality without a
        redundant second vector search
      - uses a FRESH conversation per question, so eval questions don't
        leak context into each other the way a real multi-turn chat would
    """
    chunks = retriever.retrieve(question, k=retriever.default_k)

    context_block = format_context(chunks)
    final_prompt = RAG_PROMPT_TEMPLATE.format(context=context_block, question=question)

    conversation = Conversation()
    conversation.system(SYSTEM_PROMPT)
    outgoing_messages = conversation.messages + [user(final_prompt)]

    answer = rag_provider.generate(outgoing_messages)

    eval_chunks = [
        EvalChunk(source=c.source, text=c.content, score=c.score)
        for c in chunks
    ]
    return RagResult(retrieved_chunks=eval_chunks, generated_answer=answer)


if __name__ == "__main__":
    csv_path = "docs/RFC_evaluation/rag_evaluation_dataset.csv"
    # out_path: results are written to disk as each question completes, not
    # only at the very end -- so a crash/rate-limit partway through doesn't
    # lose everything before it. max_retries/base_delay: transient errors
    # (503 UNAVAILABLE, 429 rate limit) are retried with exponential backoff
    # starting at base_delay seconds; real errors are not retried.
    results = run_evaluation(
        csv_path,
        my_rag_pipeline,
        out_path="eval_results.csv",
        max_retries=5,
        base_delay=5.0,
        verbose=True,
    )
    print(f"\nCompleted {len(results)} case(s). Results saved to eval_results.csv")
    report.print_report(results)
