# Gmail RAG Assistant 📧

Search and ask questions about your Gmail emails using AI.

## Setup

### 1. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project and enable **Gmail API**
3. Create **OAuth 2.0 Desktop Client** credentials
4. Download and save as `~/.config/gcp/langchain/credentials.json`
5. Add your email as a test user in OAuth consent screen

### 3. Configure Environment

Create `.env` file:

```env
GOOGLE_CREDENTIALS_PATH=~/.config/gcp/langchain/credentials.json
GOOGLE_TOKEN_PATH=~/.config/gcp/langchain/token.json
OPENAI_API_KEY=your_openai_api_key_here
```

Get OpenAI API key from [platform.openai.com](https://platform.openai.com/api-keys)

## Usage

### Index your emails:
```bash
python ingest_gmail_drive.py
```

### Launch UI:
```bash
python app.py
```

Open `http://localhost:7860` in your browser.

## File Structure

```
gmail_rag/
├── ingest_gmail_drive.py  # Fetch and index emails
├── app.py                 # Gradio UI
├── requirements.txt       # Dependencies
├── .env                   # API keys (create this)
└── chroma/               # Vector database (auto-created)
```

## Configuration

**Change number of emails** in `ingest_gmail_drive.py`:
```python
gmail_docs = load_gmail(n=100)  # Adjust this number
```

**Change AI model** in `app.py`:
```python
LLM_MODEL = "gpt-4o-mini"  # or "gpt-4", "gpt-3.5-turbo"
```

## Troubleshooting

- **"Access Blocked"**: Add your email as test user in Google Cloud
- **"ChromaDB not found"**: Run `ingest_gmail_drive.py` first
- **Token expired**: Delete `~/.config/gcp/langchain/token.json` and re-run

## Cost

- Embeddings: ~$0.01-0.05 per 100 emails
- Queries: ~$0.01 per 100 questions (using gpt-4o-mini)
- Gmail API: Free

## Security

Never commit: `.env`, `credentials.json`, `token.json`, `chroma/`

The `.gitignore` file protects these automatically.