# Gmail Emails Summarizer

## Project: https://github.com/AAhmeddRRagabb/Gmail-Emails-Summarization

## Project overview

This is a **personal Gmail email summarizer**. It is designed to read and summarize emails from **your own Gmail account only**, after you sign in and explicitly grant the application read-only Gmail permission through Google OAuth.

When you click **Summarize my emails**, the project follows this process:

1. Uses your Google OAuth token to connect to your Gmail account.
2. Retrieves up to five of your latest **unread Inbox emails**.
3. Extracts each email's sender, subject, date, and readable body text.
4. Sends the formatted email text to Groq through its OpenAI-compatible API.
5. Uses the LLM to group and summarize emails by sender.
6. Returns the summaries to the FastAPI frontend.
7. Shows every sender summary in a responsive card.

The project uses the Gmail scope below, which permits reading only; it cannot send, delete, label, archive, or mark your Gmail messages as read:

```text
https://www.googleapis.com/auth/gmail.readonly
```

## Setup and run

### 1. Open the project folder

Open Command Prompt or the VS Code terminal inside the project directory:

```bat
cd D:\path\to\gmail_emails_summarization
```

All following commands must run from this folder.

### 2. Install UV
```bat
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
Then, restart the terminal.


### 3. Create .venv & install dependecies

```bat
uv sync
```

### 4. Activate .venv

```bat
.venv\Scripts\activate.ps1
```

### 5. Create a Groq API key

1. Open [Groq Console](https://console.groq.com/keys).
2. Create a new API key.
3. In the project root, create a file named `.env`.
4. Add this line, replacing the value with your actual Groq key:

```env
GROQ_API_KEY=gsk_your_actual_key_here
```


### 6. Create the Gmail application in Google Cloud

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Select **APIs & Services** → **Library**.
4. Search for **Gmail API**.
5. Open it and click **Enable**.
6. Open **Google Auth platform** or **OAuth consent screen**.
7. Configure the consent screen:
   - Set an app name.
   - Select your support email.
   - Choose **External** for a personal Gmail account.
   - Keep the app in **Testing** mode.
   - Under **Test users**, add the Gmail address you will use with this project.
8. In **Data Access**, add this scope:

```text
https://www.googleapis.com/auth/gmail.readonly
```

9. Open **Clients** or **Credentials** and click **Create client**.
10. Select **Desktop app**.
11. Create the client and download its JSON credentials file.

### 7. Add the Google credentials to the project

Create the required folder if it does not already exist:

```bat
mkdir secrets
```

Move the JSON file downloaded from Google Cloud to this exact location and rename it exactly as shown:

```text
gmail_emails_summarization\secrets\credentials.json
```

Your project should now contain:

```text
gmail_emails_summarization/
├── .env
├── main.py
├── requirements.txt
├── secrets/
│   └── credentials.json
├── static/
└── templates/
```

### 8. Confirm the configuration

Open `config.py`. The project is configured to summarize five unread Inbox emails:

```python
NUMBER_OF_EMAILS_TO_SUMMARIZE = 5
```

The Gmail search filter used by the project is:

```text
in:inbox is:unread
```

This means it summarizes up to five latest unread emails in your Inbox. Change the number in `config.py` if needed.

### 9. Start the application

With `(.venv)` still active, run:

```bat
python main.py
```

Open this URL in your browser:

```text
http://127.0.0.1:8000
```

### 10. Authorize Gmail and generate a summary

1. Click **Summarize my emails**.
2. On the first request, a Google sign-in window opens.
3. Sign in with the Gmail account you added as a Google OAuth test user.
4. Approve the requested read-only Gmail permission.
5. Google returns the authorization to the app.
6. The project creates `secrets/token.json` automatically.
7. The latest unread email summaries appear as cards in the browser.

On later runs, the application uses `secrets/token.json` and should not ask you to sign in again unless the permission needs to be renewed.



