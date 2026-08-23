# Gmail Knowledge Worker

A private AI-powered chatbot that connects to your Gmail account, fetches your sent emails into a json file, then creates a vector database, and lets you query them using natural language. Built with LangChain, Chroma, OpenAI, and Gradio.

---

## How It Works

1. **Gmail API** fetches your sent emails in read-only mode
2. Email content is parsed and saved to a local JSON file
3. Emails are chunked and embedded using OpenAI's `text-embedding-3-large` model
4. Embeddings are stored in a local **Chroma** vector database
5. A **Gradio** chat interface lets you ask questions about your emails
6. Relevant emails are retrieved and passed to **GPT-4.1-nano** to generate answers



## Step 1: Set Up Gmail API Credentials

### 1.1 Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click the project dropdown at the top → **New Project**
3. Give it a name (e.g. `gmail_knowledge_worker`) and click **Create**
4. Make sure your new project is selected in the dropdown

### 1.2 Enable the Gmail API
1. In the left sidebar go to **APIs & Services** → **Library**
2. Search for **Gmail API**
3. Click on it and press **Enable**

### 1.3 Configure the OAuth Consent Screen
1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** as the user type → click **Create**
3. Fill in the required fields:
   - **App name**: `gmail_knowledge_worker`
   - **User support email**: your Gmail address
   - **Developer contact email**: your Gmail address
4. Click **Save and Continue** through the remaining steps
5. On the **Test users** section, click **Add Users**
6. Add your own Gmail address (e.g. `yourname@gmail.com`)
7. Click **Save**

### 1.4 Create OAuth 2.0 Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. Select **Desktop app** as the application type
4. Give it a name and click **Create**
5. Click **Download JSON** on the confirmation screen
6. Rename the downloaded file to `credentials.json`
7. Move it into your project folder (`geraldino/`)

---

## Step 2: Set Up OpenAI API Key

Create a `.env` file in your project folder:
```bash
touch .env
```

Add your OpenAI API key:
```
OPENAI_API_KEY=your-openai-api-key-here
```

---

## Step 3: Install Dependencies
```bash
uv pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client \
               langchain-openai langchain-chroma langchain-text-splitters \
               langchain-core gradio python-dotenv
```

---

## Step 4: Fetch Your Sent Emails
```bash
python gmail_vector_store.py
```

- A browser window opens asking you to sign in to Google
- Grant read-only access to your Gmail
- Emails are saved to `sent_emails.json`
- `token.pickle` is created for future logins

### Verify emails were fetched
```bash
python3 -c "
import json
with open('sent_emails.json') as f:
    emails = json.load(f)
with_body = [e for e in emails if e['body'].strip()]
print(f'Total emails: {len(emails)}')
print(f'Emails with body content: {len(with_body)}')
"
```

---

## Step 5: Launch the Knowledge Worker
```bash
python gmail_knowledge_worker.py
```

- Builds the vector store from your emails on first run
- Loads existing vector store instantly on subsequent runs
- Opens Gradio UI at `http://127.0.0.1:7860`

---

## Example Questions

- *"Who have I emailed about meetings?"*
- *"What did I say about the project deadline?"*
- *"Find emails where I discussed invoices"*
- *"Have I emailed anyone about vectorization?"*

---

## Rebuilding the Vector Store
```bash
rm -rf chroma_db/
python gmail_knowledge_worker.py
```

---

## Security & Privacy

- All emails stored **locally** on your machine
- Gmail accessed in **read-only** mode
- Only embeddings and queries sent to OpenAI

| File | Why it's gitignored |
|------|-----|
| `credentials.json` | Google OAuth credentials |
| `token.pickle` | Gmail access token |
| `sent_emails.json` | Your personal email content |
| `chroma_db/` | Your indexed email vectors |
| `.env` | Your API keys |

---

## Configuration

In `gmail_knowledge_worker.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `MODEL` | `gpt-4.1-nano` | OpenAI chat model |
| `RETRIEVAL_K` | `10` | Email chunks retrieved per query |
| `chunk_size` | `500` | Text chunk size for embedding |

In `gmail_vector_store.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `max_results` | `100` | Number of emails to fetch |

---

## 🐛 Common Issues

**`ModuleNotFoundError`** — Activate your virtual environment and reinstall packages.

**`Error 403: access_denied`** — Add your Gmail as a test user in OAuth consent screen (Step 1.3).

**`token.pickle` not working** — Delete and re-authenticate:
```bash
rm token.pickle
python gmail_vector_store.py
```

---


## 👨‍💻 Author

Built by **Gerald Okeke** as part of the **Andela AI Bootcamp**.

[Connect with me on LinkedIn](https://www.linkedin.com/in/gerald-nwogbo-okeke/)