"""
Gmail Vector Store Builder
Connects to Gmail API using credentials.json, fetches sent emails,
and builds a vector database using Ollama and Chroma.
"""

import os
import pickle
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
# from google.api_core.exceptions import HttpError
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
import json

# Gmail API that allows only read-only access to emails. This is the scope of the credentials.json file.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle' # This is the file that stores the credentials for the next time the script is run.

class GmailVectorStore:
    def __init__(self):
        self.service = None
        self.emails = []
        
    def authenticate(self):
        """Authenticate with Gmail API using credentials.json"""
        creds = None
        
        # Load existing token if available
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, it gets new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("✓ Successfully authenticated with Gmail API")
        return self.service
    
    def get_sent_emails(self, max_results=50):
        """
        Fetch sent emails from Gmail
        
        Args:
            max_results: Maximum number of emails to fetch
        """
        try:
            # Query 'SENT items' from the Gmail API
            results = self.service.users().messages().list(
                userId='me',
                q='label:SENT',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            print(f"✓ Found {len(messages)} sent emails")
            
            # Gets full details of the mail
            for msg_id_dict in messages:
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg_id_dict['id'],
                    format='full'
                ).execute()
                
                email_data = self._parse_message(message)
                if email_data:
                    self.emails.append(email_data)
            
            print(f"✓ Fetched {len(self.emails)} emails with full details")
            return self.emails
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def _parse_message(self, message):
        """Parse Gmail message into structured data"""
        try:
            headers = message['payload']['headers']
            
            # Extract key headers
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            from_addr = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            to_addr = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            
            # Extract body of the mail
            body = self._get_message_body(message['payload'])
            
            return {
                'id': message['id'],
                'subject': subject,
                'from': from_addr,
                'to': to_addr,
                'date': date,
                'body': body,
                'full_text': f"Subject: {subject}\nTo: {to_addr}\n\n{body}"
            }
        except Exception as e:
            print(f"Error parsing message: {e}")
            return None

    def _get_message_body(self, payload):
        """Extract body text from Gmail message payload"""
        import re
        
        def decode_data(data):
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        def strip_html(html):
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        
        def extract_from_parts(parts):
            plain_text = ''
            html_text = ''
            for part in parts:
                mime_type = part.get('mimeType', '')
                data = part.get('body', {}).get('data', '')
                
                # Recurse into nested multipart
                if mime_type.startswith('multipart') and 'parts' in part:
                    nested_plain, nested_html = extract_from_parts(part['parts'])
                    plain_text += nested_plain
                    html_text += nested_html
                
                elif mime_type == 'text/plain' and data:
                    plain_text += decode_data(data)
                
                elif mime_type == 'text/html' and data:
                    html_text += strip_html(decode_data(data))
            
            return plain_text, html_text
        
        if 'parts' in payload:
            plain, html = extract_from_parts(payload['parts'])
            # Prefer plain text, fall back to stripped HTML
            return plain.strip() if plain.strip() else html.strip()
        else:
            data = payload.get('body', {}).get('data', '')
            if data:
                decoded = decode_data(data)
                if payload.get('mimeType') == 'text/html':
                    return strip_html(decoded)
                return decoded.strip()
        
        return ''
    
    def save_emails_to_json(self, filename='sent_emails.json'):
        """Save fetched emails to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.emails, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved {len(self.emails)} emails to {filename}")


def main():
    """Main execution"""
    print("=" * 50)
    print("Gmail Vector Store Builder")
    print("=" * 50)
    
    # Initialize and authenticate
    store = GmailVectorStore()
    store.authenticate()
    
    # Gets sent emails
    print("\nFetching sent emails...")
    store.get_sent_emails(max_results=50)  # Starts with 50, increases as needed
    
    # Saves emails to JSON
    store.save_emails_to_json()
    
    print("\n" + "=" * 50)
    print("Next steps:")
    print("1. Install: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    print("2. Make sure your credentials.json is in the same directory")
    print("3. Run: python gmail_vector_store.py")
    print("=" * 50)


if __name__ == '__main__':
    main()