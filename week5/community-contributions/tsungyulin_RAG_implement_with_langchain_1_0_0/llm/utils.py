import os
import numpy as np
import glob
from sklearn.manifold import TSNE
import plotly.graph_objects as go
from typing import List

from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

DB_NAME = "vector_db"


def getKnowledgeDoc(folder: str = "knowledge-base"):
    stockFolders = glob.glob(f"{folder}/*")
    documents = []
    for sf in stockFolders:
        stockNum = os.path.basename(sf)
        loader = DirectoryLoader(
            sf, glob="**/*.md", loader_cls=TextLoader, recursive=True)
        folderDocs = loader.load()
        for doc in folderDocs:
            doc.metadata["stock_num"] = stockNum
            documents.append(doc)

    return documents


def doc2chunk(documents: List, chunk_size: int, overlap: int):
    spliter = CharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=overlap)
    return spliter.split_documents(documents)


def text2embedding(chunks) -> Chroma:
    embeddings = OpenAIEmbeddings()
    # Delete old database
    if os.path.exists(DB_NAME):
        Chroma(persist_directory=DB_NAME,
               embedding_function=embeddings).delete_collection()
    # Create database
    vectorStore = Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=DB_NAME)

    return vectorStore


def visualizeVector(vector_store: Chroma):
    collection = vector_store._collection
    results = collection.get(include=["embeddings", "documents", "metadatas"])
    vectors = np.array(results["embeddings"])
    documents = results["documents"]
    stockTypes = [m["stock_num"] for m in results["metadatas"]]
    colors = ["blue", "orange", "red", "green", "brown"]

    tsne = TSNE(n_components=2, random_state=42, perplexity=20)
    reducedVectors = tsne.fit_transform(vectors)

    # Create the 2D scatter plot
    fig = go.Figure(data=[go.Scatter(
        x=reducedVectors[:, 0],
        y=reducedVectors[:, 1],
        mode='markers',
        marker=dict(size=5, color=colors, opacity=0.8),
        text=[f"Type: {t}<br>Text: {d[:100]}..." for t,
              d in zip(stockTypes, documents)],
        hoverinfo='text'
    )])

    fig.update_layout(
        title='2D Chroma Vector Store Visualization',
        scene=dict(xaxis_title='x', yaxis_title='y'),
        width=800,
        height=600,
        margin=dict(r=20, b=10, l=10, t=40)
    )

    fig.show()
