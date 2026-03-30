# RAG - Document Question-Answering System


🚀 A Retrieval-Augmented Generation (RAG) powered chat interface for document Q&A




## Overview
This application provides an interactive chat interface that allows users to ask questions about their documents. It combines the power of Large Language Models with document retrieval to provide accurate, source-backed answers.


Features;

- RAG-Powered Responses: Leverages document context to provide accurate, factual answers

- Flexible Query Modes: Switch between RAG and vanilla LLM responses

- Source Citations: Automatically includes relevant document sources and page numbers

- Interactive Interface: Clean, user-friendly Gradio-based chat interface

- Context Visibility: View the retrieved document chunks used to generate responses

Technical Details;

- Built with Langchain and Gradio
- Uses Arcee Conductor API for LLM capabilities
- Document embedding via BAAI/bge-small-en-v1.5
- ChromaDB for vector storage
- Supports PDF document processing