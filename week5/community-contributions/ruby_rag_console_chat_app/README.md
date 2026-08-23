# Local RAG Knowledge Base with Llama 3.2, Chroma, and Ruby
![Diagram](./doc/ruby_rag_diagram.png)

## Project Overview

This mini project demonstrates building a local Retrieval-Augmented Generation (RAG) system using the Llama 3.2 language model (via Ollama locally), Chroma vector database, and Ruby. The project includes:

- Reading and processing a knowledge base consisting of markdown files organized in folders.
- Splitting documents into context-preserving chunks using the `pragmatic_segmenter` gem for sentence-aware chunking.
- Generating semantic embeddings of chunks with Llama 3.2 local model via an OpenAI-compatible API (Ollama).
- Storing embeddings along with metadata and documents into a Chroma vector database collection.
- Performing similarity search in Chroma on user queries to retrieve relevant context.
- Constructing a conversational prompt by combining chat history, retrieved context, and user input.
- Streaming responses from the Llama 3.2 model back to the console for real-time interaction.

---

## What Has Been Done

- **Folder crawler and document loader:**  
  Recursively read all markdown files in the `knowledge_base` directory, assigning document type metadata from folder names.

- **Smart text chunking:**  
  Integrated the [`pragmatic_segmenter`](https://github.com/diasks2/pragmatic_segmenter) gem to split texts into sentence-safe chunks (~1000 characters) with overlaps to preserve context and avoid cutting sentences unnaturally.

- **Embeddings generation:**  
  Leveraged the local Llama 3.2 model via Ollama's OpenAI-compatible streaming API to generate embeddings of all text chunks, enabling efficient semantic search.

- **Chroma vector store integration:**  
  Used the `chroma-db` Ruby gem with a locally hosted Chroma server (via Docker Compose) to store embeddings and metadata, and to perform similarity search queries.

- **Interactive conversational loop:**  
  Maintained chat history manually as an array of message hashes, combined with relevant retrieved chunks to form prompts fed into the Llama 3.2 model.

- **Streaming chat responses:**  
  Implemented real-time streaming of LLM output to the console leveraging the Ruby OpenAI gem streaming feature and Ollama's compatible API.

---

## Tricky Findings & Gotchas

- **Ruby Next transpilation required for `chroma-db` gem:**  
  The gem uses modern Ruby features and requires `gem 'ruby-next'` with `require "ruby-next/language/runtime"` loaded early to avoid LoadErrors.

- **Chroma API version compatibility:**  
  Different Chroma server versions expose different API versions (`v1` vs `v2`). The `chroma-db` Ruby gem expected v2 endpoints. Using matched versions of Chroma server and the gem, or a forked gem branch with v2 support, was crucial.

- **Bundler context for scripts:**  
  Running scripts must be done with `bundle exec` or with `require 'bundler/setup'` to load local gem dependencies correctly (especially forked gems).

- **Manual management of conversational memory:**  
  Unlike Python LangChain, no high-level Ruby library exists for conversation memory or RAG chains, so that had to be implemented as arrays of messages, and prompt assembly was manual.

- **Text chunking with `pragmatic_segmenter`:**  
  Using sentence segmentation improved context retention significantly over naïve character splitting, but required careful assembly of chunks and overlaps.

- **Streaming outputs handled via custom block in Ruby OpenAI gem:**  
  Streaming integration required capturing delta chunks from the streaming API and printing them in realtime, instead of waiting for full response.

---

## Setup Instructions

### Requirements

- Ruby 3.2.x
- Bundler
- Docker & Docker Compose
- Ollama installed and running locally with the `llama3.2` model pulled
- Basic terminal shell (macOS, Linux recommended)

### Steps

1. **Clone/Fork the repository:**
2. Run `bundle install` to install Ruby dependencies
3. Run `docker compose up -d` to boot up Chroma DB
4. Run `ollama run llama3.2` to boot up Open Source LLM
5. Run `bundle exec ruby seed.rb` to seed Chroma DB with chunks of data from `knowledge_base` folder
6. Run `bundle exec ruby main.rb` to start actual conversation

### Questions to try on
1. What is the company name?
2. When the company was establised?
3. Which techologies does the company use?
4. Tell me the emplooees` names and their titles?
5. Who knows how to work with IOS?
6. Tell me who was the client for web project?
7. Is the company looking for IOS developer?

Then you can compare it with the actual knowledge base.