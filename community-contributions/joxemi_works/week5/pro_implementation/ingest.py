from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from chromadb import PersistentClient
from tqdm import tqdm
from litellm import completion
from multiprocessing import Pool
from tenacity import retry, wait_exponential


# Carga variables de entorno desde .env (por ejemplo API keys)
load_dotenv(override=True)

MODEL = "openai/gpt-4.1-nano"

# Rutas base del proyecto (igual que el archivo original, solo con comentarios)
DB_NAME = str(Path(__file__).parent.parent / "preprocessed_db")
collection_name = "docs"
#embedding_model = "text-embedding-3-large"
embedding_model ="all-MiniLM-L6-v2"
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge-base"
AVERAGE_CHUNK_SIZE = 100
wait = wait_exponential(multiplier=1, min=10, max=240)


WORKERS = 3

openai = OpenAI()


class Result(BaseModel):
    # Texto final indexable en el vector store
    page_content: str
    # Metadatos para trazabilidad (origen y tipo)
    metadata: dict


class Chunk(BaseModel):
    # Titulo corto orientado a mejorar retrieval
    headline: str = Field(
        description="A brief heading for this chunk, typically a few words, that is most likely to be surfaced in a query",
    )
    # Resumen breve para ayudar a responder preguntas
    summary: str = Field(
        description="A few sentences summarizing the content of this chunk to answer common questions"
    )
    # Texto original sin modificar
    original_text: str = Field(
        description="The original text of this chunk from the provided document, exactly as is, not changed in any way"
    )

    # Convierte chunk de LLM al formato final de almacenamiento
    def as_result(self, document):
        metadata = {"source": document["source"], "type": document["type"]}
        return Result(
            page_content=self.headline + "\n\n" + self.summary + "\n\n" + self.original_text,
            metadata=metadata,
        )


class Chunks(BaseModel):
    # El LLM responde como: {"chunks": [...]} 
    chunks: list[Chunk]


def fetch_documents():
    """Recorre knowledge-base y carga todos los .md."""

    documents = []

    # Cada subcarpeta se considera un tipo documental
    for folder in KNOWLEDGE_BASE_PATH.iterdir():
        doc_type = folder.name
        # Lee markdowns recursivamente
        for file in folder.rglob("*.md"):
            with open(file, "r", encoding="utf-8") as f:
                documents.append({"type": doc_type, "source": file.as_posix(), "text": f.read()})

    print(f"Loaded {len(documents)} documents")
    return documents


def make_prompt(document):
    # Estima cuantos chunks pedir segun longitud del documento
    how_many = (len(document["text"]) // AVERAGE_CHUNK_SIZE) + 1
    return f"""
You take a document and you split the document into overlapping chunks for a KnowledgeBase.

The document is from the shared drive of a company called Insurellm.
The document is of type: {document["type"]}
The document has been retrieved from: {document["source"]}

A chatbot will use these chunks to answer questions about the company.
You should divide up the document as you see fit, being sure that the entire document is returned across the chunks - don't leave anything out.
This document should probably be split into at least {how_many} chunks, but you can have more or less as appropriate, ensuring that there are individual chunks to answer specific questions.
There should be overlap between the chunks as appropriate; typically about 25% overlap or about 50 words, so you have the same text in multiple chunks for best retrieval results.

For each chunk, you should provide a headline, a summary, and the original text of the chunk.
Together your chunks should represent the entire document with overlap.

Here is the document:

{document["text"]}

Respond with the chunks.
"""


def make_messages(document):
    # Formato de mensajes esperado por el modelo
    return [
        {"role": "user", "content": make_prompt(document)},
    ]


# Reintenta automaticamente con backoff exponencial ante errores temporales
@retry(wait=wait)
def process_document(document):
    messages = make_messages(document)
    response = completion(model=MODEL, messages=messages, response_format=Chunks)
    reply = response.choices[0].message.content
    # Valida y parsea JSON a objetos Pydantic
    doc_as_chunks = Chunks.model_validate_json(reply).chunks
    return [chunk.as_result(document) for chunk in doc_as_chunks]


def create_chunks(documents):
    """
    Crea chunks en paralelo.
    Si hay rate limit, baja WORKERS a 1.
    """
    chunks = []
    with Pool(processes=WORKERS) as pool:
        # Recoge resultados segun terminan (no respeta orden original)
        for result in tqdm(pool.imap_unordered(process_document, documents), total=len(documents)):
            chunks.extend(result)
    return chunks


def create_embeddings(chunks):
    chroma = PersistentClient(path=DB_NAME)
    if collection_name in [c.name for c in chroma.list_collections()]:
        # Borra coleccion previa para reconstruir vectorstore
        chroma.delete_collection(collection_name)

    texts = [chunk.page_content for chunk in chunks]
    emb = openai.embeddings.create(model=embedding_model, input=texts).data
    vectors = [e.embedding for e in emb]

    collection = chroma.get_or_create_collection(collection_name)

    ids = [str(i) for i in range(len(chunks))]
    metas = [chunk.metadata for chunk in chunks]

    collection.add(ids=ids, embeddings=vectors, documents=texts, metadatas=metas)
    print(f"Vectorstore created with {collection.count()} documents")


if __name__ == "__main__":
    # Pipeline completo: cargar docs, chunkear, vectorizar y guardar
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion complete")


