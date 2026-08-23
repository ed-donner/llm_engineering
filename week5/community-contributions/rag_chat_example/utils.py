from chromadb import PersistentClient
from dotenv import load_dotenv
from enum import Enum

import plotly.graph_objects as go
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
import numpy as np
import os
from pathlib import Path
from sklearn.manifold import TSNE
from typing import Any, List, Tuple, Generator

cur_path = Path(__file__)
env_path = cur_path.parent.parent.parent.parent / '.env'
assert env_path.exists(), f"Please add an .env to the root project path"

load_dotenv(dotenv_path=env_path)


class Rag(Enum):

    GPT_MODEL = "gpt-4o-mini"
    HUG_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBED_MODEL = OpenAIEmbeddings()
    DB_NAME = "vector_db"


def add_metadata(doc: Document, doc_type: str) -> Document:
    """
    Add metadata to a Document object.

    :param doc: The Document object to add metadata to.
    :type doc: Document
    :param doc_type: The type of document to be added as metadata.
    :type doc_type: str
    :return: The Document object with added metadata.
    :rtype: Document
    """
    doc.metadata["doc_type"] = doc_type
    return doc


def get_chunks(folders: Generator[Path, None, None], file_ext='.txt') -> List[Document]:
    """
    Load documents from specified folders, add metadata, and split them into chunks.

    :param folders: List of folder paths containing documents.
    :type folders: List[str]
    :param file_ext:
        The file extension to get from a local knowledge base (e.g. '.txt')
    :type file_ext: str
    :return: List of document chunks.
    :rtype: List[Document]
    """
    text_loader_kwargs = {'encoding': 'utf-8'}
    documents = []
    for folder in folders:
        doc_type = os.path.basename(folder)
        loader = DirectoryLoader(
            folder, glob=f"**/*{file_ext}", loader_cls=TextLoader, loader_kwargs=text_loader_kwargs
        )
        folder_docs = loader.load()
        documents.extend([add_metadata(doc, doc_type) for doc in folder_docs])

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)

    return chunks


def create_vector_db(db_name: str, chunks: List[Document], embeddings: Any) -> Any:
    """
    Create a vector database from document chunks.

    :param db_name: Name of the database to create.
    :type db_name: str
    :param chunks: List of document chunks.
    :type chunks: List[Document]
    :param embeddings: Embedding function to use.
    :type embeddings: Any
    :return: Created vector store.
    :rtype: Any
    """
    # Delete if already exists
    if os.path.exists(db_name):
        Chroma(persist_directory=db_name, embedding_function=embeddings).delete_collection()

    # Create vectorstore
    vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=db_name)

    return vectorstore


def get_local_vector_db(path: str) -> Any:
    """
    Get a local vector database.

    :param path: Path to the local vector database.
    :type path: str
    :return: Persistent client for the vector database.
    :rtype: Any
    """
    return PersistentClient(path=path)


def get_vector_db_info(vector_store: Any) -> None:
    """
    Print information about the vector database.

    :param vector_store: Vector store to get information from.
    :type vector_store: Any
    """
    collection = vector_store._collection
    count = collection.count()

    sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
    dimensions = len(sample_embedding)

    print(f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store")


def get_plot_data(collection: Any) -> Tuple[np.ndarray, List[str], List[str], List[str]]:
    """
    Get plot data from a collection.

    :param collection: Collection to get data from.
    :type collection: Any
    :return: Tuple containing vectors, colors, document types, and documents.
    :rtype: Tuple[np.ndarray, List[str], List[str], List[str]]
    """
    result = collection.get(include=['embeddings', 'documents', 'metadatas'])
    vectors = np.array(result['embeddings'])
    documents = result['documents']
    metadatas = result['metadatas']
    doc_types = [metadata['doc_type'] for metadata in metadatas]
    colors = [['blue', 'green', 'red', 'orange'][['products', 'employees', 'contracts', 'company'].index(t)] for t in
              doc_types]

    return vectors, colors, doc_types, documents


def get_2d_plot(collection: Any) -> go.Figure:
    """
    Generate a 2D plot of the vector store.

    :param collection: Collection to generate plot from.
    :type collection: Any
    :return: 2D scatter plot figure.
    :rtype: go.Figure
    """
    vectors, colors, doc_types, documents = get_plot_data(collection)
    tsne = TSNE(n_components=2, random_state=42)
    reduced_vectors = tsne.fit_transform(vectors)

    fig = go.Figure(data=[go.Scatter(
        x=reduced_vectors[:, 0],
        y=reduced_vectors[:, 1],
        mode='markers',
        marker=dict(size=5, color=colors, opacity=0.8),
        text=[f"Type: {t}<br>Text: {d[:100]}..." for t, d in zip(doc_types, documents)],
        hoverinfo='text'
    )])

    fig.update_layout(
        title='2D Chroma Vector Store Visualization',
        scene=dict(xaxis_title='x', yaxis_title='y'),
        width=800,
        height=600,
        margin=dict(r=20, b=10, l=10, t=40)
    )

    return fig


def get_3d_plot(collection: Any) -> go.Figure:
    """
    Generate a 3D plot of the vector store.

    :param collection: Collection to generate plot from.
    :type collection: Any
    :return: 3D scatter plot figure.
    :rtype: go.Figure
    """
    vectors, colors, doc_types, documents = get_plot_data(collection)
    tsne = TSNE(n_components=3, random_state=42)
    reduced_vectors = tsne.fit_transform(vectors)

    fig = go.Figure(data=[go.Scatter3d(
        x=reduced_vectors[:, 0],
        y=reduced_vectors[:, 1],
        z=reduced_vectors[:, 2],
        mode='markers',
        marker=dict(size=5, color=colors, opacity=0.8),
        text=[f"Type: {t}<br>Text: {d[:100]}..." for t, d in zip(doc_types, documents)],
        hoverinfo='text'
    )])

    fig.update_layout(
        title='3D Chroma Vector Store Visualization',
        scene=dict(xaxis_title='x', yaxis_title='y', zaxis_title='z'),
        width=900,
        height=700,
        margin=dict(r=20, b=10, l=10, t=40)
    )

    return fig


def get_conversation_chain(vectorstore: Any) -> ConversationalRetrievalChain:
    """
    Create a conversation chain using the vector store.

    :param vectorstore: Vector store to use in the conversation chain.
    :type vectorstore: Any
    :return: Conversational retrieval chain.
    :rtype: ConversationalRetrievalChain
    """
    llm = ChatOpenAI(temperature=0.7, model_name=Rag.GPT_MODEL.value)

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key='answer')

    retriever = vectorstore.as_retriever(search_kwargs={"k": 25})

    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
    )

    return conversation_chain


def get_lang_doc(document_text, doc_id, metadata=None, encoding='utf-8'):

    """
    Build a langchain Document that can be used to create a chroma database

    :type document_text: str
    :param document_text:
        The text to add to a document object
    :type doc_id: str
    :param doc_id:
        The document id to include.
    :type metadata: dict
    :param metadata:
        A dictionary of metadata to associate to the document object. This will help filter an item from a
        vector database.
    :type encoding: string
    :param encoding:
        The type of encoding to use for loading the text.

    """
    return Document(
        page_content=document_text,
        id=doc_id,
        metadata=metadata,
        encoding=encoding,
    )


