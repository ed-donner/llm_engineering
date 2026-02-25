from openai import OpenAI
from dotenv import load_dotenv
from chromadb import PersistentClient
from litellm import completion
from pydantic import BaseModel, Field
from pathlib import Path
from tenacity import retry, wait_exponential


# Carga variables de entorno (.env), por ejemplo claves de APIs
load_dotenv(override=True)

# Modelo para tareas de razonamiento/generacion y utilidades (rewrite/rerank/answer)
# MODEL = "openai/gpt-4.1-nano"
MODEL = "groq/openai/gpt-oss-120b"

# Rutas base del proyecto (igual que el archivo original, solo con comentarios)
DB_NAME = str(Path(__file__).parent.parent / "preprocessed_db")
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge-base"
SUMMARIES_PATH = Path(__file__).parent.parent / "summaries"

collection_name = "docs"
#embedding_model = "text-embedding-3-large"
embedding_model ="all-MiniLM-L6-v2"
# Reintento exponencial para errores transitorios (timeouts, rate limits, etc.)
wait = wait_exponential(multiplier=1, min=10, max=240)

openai = OpenAI()

# Conecta con Chroma y carga (o crea) la coleccion vectorial
chroma = PersistentClient(path=DB_NAME)
collection = chroma.get_or_create_collection(collection_name)

# Cantidad de chunks recuperados inicialmente
RETRIEVAL_K = 20
# Cantidad final de chunks que se pasan al LLM para responder
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
    # Contenido textual del chunk recuperado
    page_content: str
    # Metadatos (por ejemplo source/type)
    metadata: dict


class RankOrder(BaseModel):
    # Lista de IDs de chunks en orden de relevancia (1 = mas relevante)
    order: list[int] = Field(
        description="The order of relevance of chunks, from most relevant to least relevant, by chunk id number"
    )


@retry(wait=wait)
def rerank(question, chunks):
    # Prompt para reordenar chunks por relevancia respecto a la pregunta
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
    # Convierte IDs 1-based del modelo a indices 0-based de Python
    return [chunks[i - 1] for i in order]


def make_rag_messages(question, history, chunks):
    # Construye el contexto concatenando extractos de cada chunk recuperado
    context = "\n\n".join(
        f"Extract from {chunk.metadata['source']}:\n{chunk.page_content}" for chunk in chunks
    )
    system_prompt = SYSTEM_PROMPT.format(context=context)
    # Mensajes finales: system + historial + pregunta actual
    return (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": question}]
    )


@retry(wait=wait)
def rewrite_query(question, history=[]):
    """Reescribe la pregunta para mejorar la busqueda en la Knowledge Base."""
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
    response = completion(model=MODEL, messages=[{"role": "system", "content": message}])
    return response.choices[0].message.content


def merge_chunks(chunks, reranked):
    # Fusiona dos listas de chunks evitando duplicados por texto exacto
    merged = chunks[:]
    existing = [chunk.page_content for chunk in chunks]
    for chunk in reranked:
        if chunk.page_content not in existing:
            merged.append(chunk)
    return merged


def fetch_context_unranked(question):
    # Embedding de la pregunta para buscar semantica en la coleccion vectorial
    query = openai.embeddings.create(model=embedding_model, input=[question]).data[0].embedding
    results = collection.query(query_embeddings=[query], n_results=RETRIEVAL_K)
    chunks = []
    for result in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append(Result(page_content=result[0], metadata=result[1]))
    return chunks


def fetch_context(original_question):
    # Estrategia hibrida:
    # 1) busca con pregunta original,
    # 2) busca con pregunta reescrita,
    # 3) combina y reranquea,
    # 4) se queda con los FINAL_K mejores.
    rewritten_question = rewrite_query(original_question)
    chunks1 = fetch_context_unranked(original_question)
    chunks2 = fetch_context_unranked(rewritten_question)
    chunks = merge_chunks(chunks1, chunks2)
    reranked = rerank(original_question, chunks)
    return reranked[:FINAL_K]


@retry(wait=wait)
def answer_question(question: str, history: list[dict] = []) -> tuple[str, list]:
    """
    Responde con RAG y devuelve: (respuesta, contexto recuperado).
    """
    chunks = fetch_context(question)
    messages = make_rag_messages(question, history, chunks)
    response = completion(model=MODEL, messages=messages)
    return response.choices[0].message.content, chunks


