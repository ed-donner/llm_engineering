🔎 Data Lineage Search RAG App (Streamlit + Gradio)

This project is a data lineage and search RAG application that allows users to search for:

Columns
Tables
SQL transformations
Mapping metadata

It supports both Streamlit and Gradio UIs and is powered by a FastAPI backend.

🚀 Features
🔍 Search across mapping files and SQL scripts
🧠 Understand complex DMLs and transformations
📊 View structured lineage and metadata

🖥️ Dual UI support:
Streamlit (interactive dashboard)
Gradio (lightweight UI)
⚡ FastAPI backend for scalable processing

🏗️ Architecture
Frontend
Streamlit UI (ui/streamlit_app.py)
Gradio UI (ui/gradio_app.py)
Backend
FastAPI service (api/app.py)
Processing
SQL parsing and lineage extraction
Mapping file interpretation
Optional LLM support via OpenAI
Mapping file and SQL files interpretation using LLM via OpenAI

Adding Data:
Create a folder data at the same level as api or ingestion, and add your sql files and csv,xslx,xsl files.

📦 Prerequisites
Python 3.10+
uv package manager
⚙️ Installation
1. Install uv
pip install uv
2. Install Dependencies
uv pip install -r requirements.txt
3. Configure Environment Variables

Create a .env file in the root directory:

OPEN_API_KEY=your_openai_api_key_here
▶️ Running the Application
1. Start the FastAPI Backend
uvicorn api.app:app --reload

Backend will be available at:

http://localhost:8000
2. Run Streamlit UI
uv run streamlit run ui/streamlit_app.py
3. Run Gradio UI
uv run ui/gradio_app.py

🧪 Usage
Enter a table name or column name in the search bar
The system will:
Search mapping files
Analyze SQL scripts
Return lineage and metadata
View results in structured format (tables, lineage graphs, etc.)
