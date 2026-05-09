# Tools and Libraries Reference

## OpenAI Python SDK
The primary client for calling OpenAI models and any OpenAI-compatible API. Install with `pip install openai`. Create a client with `OpenAI()` which reads the OPENAI_API_KEY environment variable. For other providers, pass `base_url` and `api_key` parameters.

## OpenRouter
A unified API gateway that provides access to many LLM providers (Anthropic, Google, Meta, Mistral) through a single API key. Uses the OpenAI-compatible client pattern. Set base_url to "https://openrouter.ai/api/v1" and use your OPENROUTER_API_KEY. Model names follow the format "provider/model-name".

## Gradio
A Python library for building ML demos and web UIs. Key components used in our projects:
- **gr.ChatInterface**: Quick chatbot UI with built-in message history
- **gr.Code**: Code editor panels with syntax highlighting
- **gr.themes**: Pre-built themes like Monochrome, Soft
- **gr.Blocks**: Low-level layout for custom UIs with rows and columns
- **Streaming**: Use yield in your function to stream tokens
- **type="messages"**: Use the OpenAI-compatible message format

## LangChain
A framework for building LLM applications. Key components for RAG:
- **DirectoryLoader + TextLoader**: Load documents from folders
- **RecursiveCharacterTextSplitter**: Split documents into overlapping chunks
- **ChatOpenAI**: LangChain wrapper around OpenAI's chat API
- **Chroma (langchain_chroma)**: LangChain integration with ChromaDB
- **HuggingFaceEmbeddings**: Use HuggingFace embedding models via LangChain
- All LangChain objects implement `.invoke()` for a consistent interface

## ChromaDB
An open-source vector database. Stores embeddings and supports similarity search. Can run locally with `PersistentClient(path="db_name")`. Key operations: add documents, query by embedding, get all documents. Supports metadata filtering.

## HuggingFace
- **Hub**: Repository of models, datasets, and spaces
- **Transformers**: Library for loading and running models locally
- **all-MiniLM-L6-v2**: A popular small embedding model (384 dimensions, fast, free)
- **BitsAndBytesConfig**: Configuration for 4-bit/8-bit quantization

## LiteLLM
A unified interface for calling 100+ LLMs with the same API. Supports OpenAI, Anthropic, Cohere, and more. The `completion()` function works like OpenAI's but routes to any provider. Supports structured outputs via `response_format` parameter.

## Pydantic
Data validation library used for structured outputs from LLMs. Define a `BaseModel` class with typed fields and descriptions. Pass it as `response_format` to force the LLM to output valid JSON matching your schema. Used in day5 for Chunk and RankOrder models.

## scikit-learn (t-SNE)
t-SNE (t-distributed Stochastic Neighbor Embedding) reduces high-dimensional vectors to 2D or 3D for visualization. Import from `sklearn.manifold.TSNE`. Helps visualize how well your embedding model clusters similar documents together.

## tiktoken
OpenAI's tokenizer library. Use `encoding_for_model(model_name)` to get the right tokenizer. Useful for counting tokens before sending to the API (cost estimation, context window management).
