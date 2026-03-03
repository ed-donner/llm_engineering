# AI SQL Query Builder

A practical tool that converts natural language descriptions into SQL queries using AI models. Perfect for developers, data analysts, and anyone working with databases.

## Features

- **Natural Language to SQL**: Describe what you want in plain English, get SQL queries
- **Multi-Model Support**: Access GPT, Claude, Gemini, DeepSeek, and 100+ models via OpenRouter
- **Query Explanation**: Understand what each generated query does
- **Query Optimization**: Get suggestions to improve query performance
- **Multiple SQL Dialects**: PostgreSQL, MySQL, SQLite, SQL Server
- **Complex Queries**: Handles JOINs, subqueries, aggregations, CTEs, and more
- **Schema Awareness**: Provide your table schema for accurate queries

## What It Does

**Input (Natural Language):**
```
Get all users who made a purchase in the last 30 days,
show their name, email, and total amount spent
```

**Output (SQL Query):**
```sql
SELECT
    u.name,
    u.email,
    SUM(o.amount) as total_spent
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.created_at >= NOW() - INTERVAL '30 days'
GROUP BY u.id, u.name, u.email
ORDER BY total_spent DESC;
```

## Prerequisites

- Python 3.8+
- OpenRouter API key (get free credits at [openrouter.ai](https://openrouter.ai))

## Installation

1. Navigate to this directory:

```bash
cd week4/community-contributions/dc_dalin
```

2. Create a `.env` file in the root `llm_engineering` directory with your API key:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

3. Install dependencies (if not already installed):

```bash
uv add openai python-dotenv gradio
```

## Usage

### Option 1: Interactive UI (Recommended for Demo)

1. Open the notebook:
```bash
jupyter notebook sql_query_builder.ipynb
```

2. Run all cells to launch the Gradio UI

3. Use the beautiful web interface with 4 tabs:
   - **✨ Generate SQL**: Convert natural language to SQL
   - **📚 Explain SQL**: Understand existing queries
   - **⚡ Optimize SQL**: Get performance improvements
   - **🔬 Compare Models**: See how different AI models handle the same query

### Option 2: Direct Code Usage

Run cells individually in the notebook to use functions programmatically

## Use Cases

### 1. Quick Query Generation
"Find all customers from California who spent more than $1000"

### 2. Complex Analytics
"Calculate the month-over-month growth rate for each product category"

### 3. Data Cleaning
"Find duplicate email addresses in the users table"

### 4. Query Optimization
Paste a slow query and get optimization suggestions

### 5. Learning SQL
Great for beginners to understand how SQL queries work

## Supported SQL Operations

- **SELECT**: Simple and complex queries
- **JOIN**: INNER, LEFT, RIGHT, FULL OUTER
- **Aggregations**: COUNT, SUM, AVG, MIN, MAX
- **Subqueries**: Nested queries and CTEs
- **Window Functions**: ROW_NUMBER, RANK, LAG, LEAD
- **INSERT/UPDATE/DELETE**: Data manipulation
- **CREATE/ALTER**: Schema operations
- **Indexes**: Index recommendations

## Database Dialects

- PostgreSQL (default)
- MySQL
- SQLite
- SQL Server (T-SQL)
- Oracle

## Available Models

OpenRouter gives you access to 100+ models. Popular choices:
- **GPT-5** (`openai/gpt-5`): Best for complex queries with multiple JOINs
- **Claude Sonnet 4.5** (`anthropic/claude-sonnet-4.5`): Excellent at query optimization
- **Gemini 2.5 Pro** (`google/gemini-2.5-pro`): Great for explaining queries
- **DeepSeek Chat** (`deepseek/deepseek-chat`): Fast and cost-effective
- **Qwen 2.5 Coder** (`qwen/qwen-2.5-coder-32b-instruct`): Specialized for code

## Examples Included

The notebook includes real-world examples:

1. **E-commerce Analytics**
   - Customer lifetime value calculation
   - Product performance analysis
   - Cart abandonment tracking

2. **User Behavior Analysis**
   - Active user metrics
   - Retention analysis
   - Cohort analysis

3. **Financial Reports**
   - Revenue aggregations
   - Transaction summaries
   - Period-over-period comparisons

4. **Data Quality**
   - Finding duplicates
   - Null value analysis
   - Data validation queries

## Schema Support

Provide your database schema for accurate queries:

```python
schema = """
users (id, name, email, created_at)
orders (id, user_id, amount, status, created_at)
products (id, name, price, category)
order_items (id, order_id, product_id, quantity)
"""
```

The AI will use this to generate accurate table names, column names, and relationships.

## Tips for Best Results

1. **Be Specific**: More details = better queries
2. **Mention Performance**: Add "optimized" or "efficient" for better queries
3. **Specify Dialect**: Mention PostgreSQL, MySQL, etc. if needed
4. **Include Schema**: Always helps with accuracy
5. **Ask for Explanation**: Use the explain feature to learn

## Cost Considerations

OpenRouter provides transparent pricing per model:
- **Premium models** (GPT-5, Claude Sonnet 4.5): Best for complex queries
- **Budget models** (DeepSeek, Qwen, Llama): Great for simple queries
- **Free tier**: OpenRouter offers free credits to get started
- Check current pricing at [openrouter.ai/models](https://openrouter.ai/models)

## Project Structure

```
dc_dalin/
├── sql_query_builder.ipynb  # Main notebook
├── README.md                # This file
└── .env.example            # Environment variable template
```

## Safety Features

- Query validation warnings
- Destructive operation alerts (DROP, DELETE without WHERE)
- SQL injection risk detection
- Performance impact warnings for large tables

## Future Enhancements

- Query execution against real databases
- Visual query builder interface
- Query performance prediction
- Automated testing query generation
- Migration script generation

## Contributing

This project was created as part of the Andela AI Engineering Bootcamp Week 4.

## License

Part of the Andela AI Engineering Bootcamp curriculum.

---

**Built to make database interactions easier for everyone**
