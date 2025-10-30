import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from email.utils import parsedate_to_datetime

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
GOOGLE_CREDENTIALS_PATH = os.getenv(
    "GOOGLE_CREDENTIALS_PATH", "~/.config/gcp/langchain/credentials.json"
)
GOOGLE_TOKEN_PATH = os.getenv(
    "GOOGLE_TOKEN_PATH", "~/.config/gcp/langchain/token.json"
)

# ---- LangChain imports ----
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

# ---- Settings ----
CHROMA_DIR = "chroma"
EMBED_MODEL = "text-embedding-3-small"


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    
    token_path = os.path.expanduser(GOOGLE_TOKEN_PATH)
    creds_path = os.path.expanduser(GOOGLE_CREDENTIALS_PATH)
    
    if not os.path.exists(creds_path):
        raise FileNotFoundError(
            f"Credentials file not found at: {creds_path}\n"
            f"Please download OAuth 2.0 Client ID credentials from Google Cloud Console."
        )
    
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)


def get_header_value(headers, name):
    """Extract header value from Gmail headers list."""
    for header in headers:
        if header['name'].lower() == name.lower():
            return header['value']
    return ''


def decode_body(payload):
    """Decode email body from Gmail payload."""
    body = ""
    
    if 'body' in payload and 'data' in payload['body']:
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    
    # Handle multipart messages
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    body += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
            elif 'parts' in part:
                # Recursively handle nested parts
                body += decode_body(part)
    
    return body


def load_gmail(n=50, query=None):
    """Load Gmail messages directly using Gmail API."""
    service = get_gmail_service()
    
    # Fetch message list
    results = service.users().messages().list(
        userId='me',
        maxResults=n,
        q=query if query else ''
    ).execute()
    
    messages = results.get('messages', [])
    
    if not messages:
        print("No messages found.")
        return []
    
    print(f"Fetching {len(messages)} messages...")
    
    docs = []
    for i, msg_ref in enumerate(messages, 1):
        # Fetch full message
        msg = service.users().messages().get(
            userId='me',
            id=msg_ref['id'],
            format='full'
        ).execute()
        
        # Extract headers
        headers = msg['payload']['headers']
        subject = get_header_value(headers, 'Subject')
        sender = get_header_value(headers, 'From')
        date = get_header_value(headers, 'Date')
        to = get_header_value(headers, 'To')
        
        # Extract body
        body = decode_body(msg['payload'])
        
        # Create metadata
        metadata = {
            'source': 'gmail',
            'id': msg['id'],
            'subject': subject,
            'from': sender,
            'to': to,
            'date': date,
            'thread_id': msg.get('threadId', ''),
        }
        
        # Format content
        content = f"Subject: {subject}\n"
        content += f"From: {sender}\n"
        content += f"To: {to}\n"
        content += f"Date: {date}\n\n"
        content += body
        
        docs.append(Document(page_content=content, metadata=metadata))
        
        if i % 10 == 0:
            print(f"  Processed {i}/{len(messages)} messages...")
    
    print(f"✓ Gmail: loaded {len(docs)} documents")
    return docs


def main():
    print("Starting Gmail RAG ingestion...\n")
    
    # 1) Load Gmail documents
    gmail_docs = load_gmail(n=50)
    
    if not gmail_docs:
        print("No documents to process. Exiting.")
        return
    
    # 2) Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
    chunks = splitter.split_documents(gmail_docs)
    print(f"✓ Created {len(chunks)} chunks")
    
    # 3) Create embeddings and store in ChromaDB
    print(f"✓ Creating embeddings with {EMBED_MODEL}...")
    embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
    
    Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)
    vs = Chroma.from_documents(
        chunks, 
        embedding=embeddings, 
        persist_directory=CHROMA_DIR
    )
    vs.persist()
    
    print(f"✓ Successfully persisted ChromaDB at: {CHROMA_DIR}\n")
    print("Ingestion complete! You can now query your Gmail data.")


if __name__ == "__main__":
    main()