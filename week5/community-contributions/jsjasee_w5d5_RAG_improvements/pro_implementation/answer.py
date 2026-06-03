from openai import OpenAI
from dotenv import load_dotenv
from chromadb import PersistentClient
from litellm import completion
from pydantic import BaseModel, Field
from pathlib import Path
from tenacity import retry, wait_exponential


load_dotenv(override=True)

# MODEL = "openai/gpt-4.1-nano"
# MODEL = "groq/openai/gpt-oss-120b"
MODEL = "openrouter/openai/gpt-oss-120b"  # 🚨 LiteLLM supports ALL OpenRouter models, send model=openrouter/<your-openrouter-model> to send it to open router.
DB_NAME = str(Path(__file__).parent.parent / "preprocessed_db")
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge-base"
SUMMARIES_PATH = Path(__file__).parent.parent / "summaries"

docs_collection_name = "docs"
docs_summaries_collection_name = "doc_summaries"
global_indexes_collection_name = "global_indexes"

embedding_model = "text-embedding-3-large"
wait = wait_exponential(multiplier=1, min=10, max=240)  # using tenacity package

openai = OpenAI()

chroma = PersistentClient(path=DB_NAME)
docs_collection = chroma.get_or_create_collection(docs_collection_name)
docs_summaries_collection = chroma.get_or_create_collection(
    docs_summaries_collection_name
)
global_indexes_collection = chroma.get_or_create_collection(
    global_indexes_collection_name
)

GLOBAL_INDEX_RETRIEVAL_K = 5
DOC_SUMMARIES_RETRIEVAL_K = 10
RETRIEVAL_K = 20  # fetch 20 chunks, but only keep 10 after re-ranking
FINAL_K = 10

SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant representing the company Insurellm.
You are chatting with a user about Insurellm.
Your answer will be evaluated for accuracy, relevance and completeness, so make sure it only answers the question and fully answers it.
If you don't know the answer, say so.
For context, here are specific extracts from the Knowledge Base that might be directly relevant to the user's question:
{context}

With this context, please answer the user's question. Be accurate, relevant and complete.
"""


class Result(BaseModel):
    page_content: str
    metadata: dict


class RankOrder(BaseModel):
    order: list[int] = Field(
        description="The order of relevance of chunks, from most relevant to least relevant, by chunk id number"
    )


@retry(wait=wait)
def rerank(question, chunks):
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


def is_holistic_question(question: str) -> bool:
    """
    Return True if the question seems to require information across many documents.

    This is a simple MVP router:
    - True  -> search global_indexes first
    - False -> use normal chunk retrieval
    """
    q = question.lower()

    holistic_keywords = [
        "all",
        "every",
        "list",
        "show me",
        "give me",
        "overview",
        "summary of",
        "across",
        "company-wide",
        "company wide",
        "compare",
        "comparison",
        "which employees",
        "which products",
        "what products",
        "all products",
        "all employees",
        "all contracts",
        "all awards",
        "award winners",
        "products offered",
        "contracts with",
    ]

    return any(keyword in q for keyword in holistic_keywords)


def build_summary_query(question: str, global_results: list[Result]) -> str:
    """
    Expand the original question with top global index facts.
    This helps doc_summaries retrieval find the relevant source documents.
    """
    global_context = "\n".join(result.page_content for result in global_results)

    return f"""
Original question:
{question}

Relevant global index context:
{global_context}
""".strip()


def make_rag_messages(question, history, chunks):
    context = "\n\n".join(
        f"Extract from {chunk.metadata['source']}:\n{chunk.page_content}"
        for chunk in chunks
    )
    system_prompt = SYSTEM_PROMPT.format(context=context)
    return (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": question}]
    )


@retry(wait=wait)
def rewrite_query(question, history=[]):
    """Rewrite the user's question to be a more specific question that is more likely to surface relevant content in the Knowledge Base."""
    message = f"""
You are in a conversation with a user, answering questions about the company Insurellm.
You are about to look up information in a Knowledge Base to answer the user's question.

This is the history of your conversation so far with the user:
{history}

And this is the user's current question:
{question}

Respond only with a short, refined question that you will use to search the Knowledge Base.
It should be a VERY short specific question most likely to surface content. Focus on the question details.
IMPORTANT: Respond ONLY with the precise knowledgebase query, nothing else.
"""
    response = completion(
        model=MODEL, messages=[{"role": "system", "content": message}]
    )
    return response.choices[0].message.content


def merge_chunks(chunks, reranked):
    merged = chunks[:]
    existing = [chunk.page_content for chunk in chunks]
    for chunk in reranked:
        if chunk.page_content not in existing:
            merged.append(chunk)
    return merged


@retry(wait=wait)
def query_collection(collection, question: str, n_results: int) -> list[Result]:
    """
    Query one Chroma collection and return retrieved items as Result objects.
    """
    query_embedding = (
        openai.embeddings.create(
            model=embedding_model,
            input=[question],
        )
        .data[0]
        .embedding
    )

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )
    # print(results)  # investigate the shape
    # print(results["documents"])

    retrieved_results = []

    # why results["documents"][0] because Chroma supports multiple queries, the index 0 is the documents from the first query
    for document, metadata in zip(
        results["documents"][0],
        results["metadatas"][0],
    ):
        retrieved_results.append(
            Result(
                page_content=document,
                metadata=metadata,
            )
        )

    return retrieved_results


def fetch_chunks_for_sources(sources, max_chunks_per_source=RETRIEVAL_K):
    """
    Fetch child chunks from the docs collection for specific source files.
    This uses metadata filtering, not semantic search.
    The source was already selected by searching global indexes and document summaries.
    """

    chunks = []

    for source in sources:
        results = docs_collection.get(
            where={"source": source},
            limit=max_chunks_per_source,
            include=["documents", "metadatas"],
        )  # note we are NOT using embeddings here aka trying to map vectors.
        # this is collection.get() not collection.query()

        documents = results.get("documents", [])

        metadatas = results.get("metadatas", [])

        for document, metadata in zip(documents, metadatas):
            chunks.append(
                Result(
                    page_content=document,
                    metadata=metadata,
                )  # convert them to Result pydantic objects.
            )

    return chunks


def fetch_holistic_context(question: str) -> list[Result]:
    """
    Retrieve broad context for holistic questions.

    Flow:
    1. Search global indexes for broad cross-document facts.
    2. THEN use global indexes to build a summary query to make these document summaries more targeted. Search document summaries for relevant source documents.
    3. Extract unique source files from those summaries.
    4. Fetch detailed child chunks from the docs collection by source.
    """
    global_results = query_collection(
        global_indexes_collection,
        question,
        n_results=GLOBAL_INDEX_RETRIEVAL_K,
    )

    summary_results = query_collection(
        docs_summaries_collection,
        build_summary_query(question, global_results),  # our improved summary query
        n_results=DOC_SUMMARIES_RETRIEVAL_K,
    )

    sources = []
    seen_sources = set()

    # THERE WILL BE 10 summary results per query, we don't want duplicate chunks so the code below also filters out duplicates.
    for result in summary_results:
        source = result.metadata.get("source")

        if source and source not in seen_sources:
            sources.append(source)
            seen_sources.add(source)

    supporting_chunks = fetch_chunks_for_sources(
        sources,
        max_chunks_per_source=RETRIEVAL_K,
    )

    return (
        global_results + summary_results + supporting_chunks
    )  # we still return the global_results (global_indexes) because they sometimes contain the best cross-document summaries.


def fetch_context_unranked(question):
    query = (
        openai.embeddings.create(model=embedding_model, input=[question])
        .data[0]
        .embedding
    )
    results = docs_collection.query(query_embeddings=[query], n_results=RETRIEVAL_K)
    chunks = []
    for result in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append(Result(page_content=result[0], metadata=result[1]))
    return chunks


# this function is changed from the notebook - using the technique QUERY EXPANSION.
# previously in the notebook with query rewriting (sometimes it helps, sometimes it doesn't, like adding in the word 'insurllm' to the question, diluting the question's intent)
# we don't just discard the old query, we treat the old and new query as 2 queries and rerank the chunks returned from BOTH QUERIES. (we merge them to throw out duplicates, so the LLM model doesn't have to rank duplicate chunks)
def fetch_context(original_question):
    rewritten_question = rewrite_query(original_question)

    # check if it's a holistic question, based on user's original question (could have words like 'all') or the rewritten question (could have added or deleted the words, 'all')
    is_holistic = is_holistic_question(original_question) or is_holistic_question(
        rewritten_question
    )

    if is_holistic:
        chunks1 = fetch_holistic_context(original_question)
        chunks2 = fetch_holistic_context(rewritten_question)
    else:
        # do the normal mapping for direct fact questions.
        chunks1 = fetch_context_unranked(original_question)
        chunks2 = fetch_context_unranked(rewritten_question)

    chunks = merge_chunks(chunks1, chunks2)
    reranked = rerank(original_question, chunks)
    return reranked[:FINAL_K]  # take the top 10 after re-ranking


@retry(wait=wait)
def answer_question(question: str, history: list[dict] = []) -> tuple[str, list]:
    """
    Answer a question using RAG and return the answer and the retrieved context
    """
    chunks = fetch_context(question)
    messages = make_rag_messages(question, history, chunks)
    response = completion(model=MODEL, messages=messages)
    return response.choices[0].message.content, chunks
