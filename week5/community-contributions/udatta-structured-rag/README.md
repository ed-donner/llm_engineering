# Structured Data RAG: Semantic Search + Text-to-SQL

This notebook demonstrates two complementary approaches to answering natural language questions over structured/tabular data:

1. **Semantic Row Search** — Embed CSV rows and retrieve relevant ones via vector similarity, then answer with an LLM.
2. **Text-to-SQL** — Translate natural language queries to SQL, execute them, and return structured results.

## When to Use Each

- **Semantic Search**: Exploratory queries, fuzzy matching, narrative descriptions. Handles nuanced language well.
- **Text-to-SQL**: Aggregations, exact filters, numerical comparisons. Precise results on structured data.

## Stack

- ChromaDB for semantic embeddings (ChromaDB handles embeddings automatically)
- LangChain's SQLDatabaseChain for text-to-SQL
- gpt-4o-mini for LLM generation
- SQLite for the database backend

## Requirements

```bash
pip install pandas chromadb openai langchain langchain-community sqlalchemy python-dotenv
```

Set your `OPENAI_API_KEY` in a `.env` file.
