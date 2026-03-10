import os
from typing import List, Dict, Union
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import io
from markitdown import MarkItDown, StreamInfo

class GoogleDriveClient:
    """
    A class to read files from a Google Drive directory, convert their contents to markdown,
    and store them as a collection for later use.
    """

    SCOPES = [
        # Per-file access to files created or opened with the app (recommended for most apps)
        'https://www.googleapis.com/auth/drive.file',
        # Read-only access to all Drive files
        'https://www.googleapis.com/auth/drive.readonly',
        # View metadata for files in your Drive (read-only)
        'https://www.googleapis.com/auth/drive.metadata.readonly'
    ]

    def __init__(self, credentials_file: str, folder_id: str):
        """
        Initialize the collector with Google service account credentials and folder ID.
        Args:
            credentials_file (str): Path to the Google service account credentials JSON file.
            folder_id (str): Google Drive folder ID to read files from.
        """
        self.credentials_file = credentials_file
        self.folder_id = folder_id
        self.service = self._authenticate()
        self.collection = {}
        self.entire_knowledge_base = ""

    def _authenticate(self):
        """
        Authenticate with Google Drive API using service account credentials.
        Returns:
            googleapiclient.discovery.Resource: Authenticated Drive API service.
        """
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return build('drive', 'v3', credentials=creds)

    def list_files(self) -> List[Dict]:
        """
        List files in the specified Google Drive folder.
        Returns:
            List[Dict]: List of file metadata dictionaries.
        """
        query = f"'{self.folder_id}' in parents and trashed = false"
        results = self.service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        return results.get('files', [])

    def read_file_raw(self, file_id: str) -> bytes:
        """
        Read the raw bytes of a file from Google Drive.
        """
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read()

    def read_file(self, file_id: str) -> str:
        """
        Read the contents of a text file from Google Drive as a string.
        For binary files (PDF, etc.), use read_file_raw() and convert_to_markdown().
        """
        raw = self.read_file_raw(file_id)
        encodings = ('utf-8', 'utf-8-sig', 'cp1252', 'latin-1', 'iso-8859-1')
        for encoding in encodings:
            try:
                return raw.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        return raw.decode('utf-8', errors='replace')

    def _mime_to_extension(self, mime_type: str) -> str:
        """Map MIME type to file extension for MarkItDown."""
        mapping = {
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'text/plain': '.txt',
        }
        return mapping.get(mime_type, '')

    def convert_to_markdown(
        self, content: Union[str, bytes], mime_type: str, filename: str = ""
    ) -> str:
        """
        Convert file content to markdown format.
        For binary files (PDF, etc.), pass raw bytes. For text, pass str.
        """
        ext = self._mime_to_extension(mime_type) or (
            os.path.splitext(filename)[1] if filename else ""
        )
        binary_mimes = ('application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')

        # Binary types: pass BytesIO to MarkItDown (expects path or binary stream)
        if mime_type in binary_mimes and ext:
            if isinstance(content, str):
                content = content.encode('latin-1', errors='replace')
            stream = io.BytesIO(content)
            md = MarkItDown()
            result = md.convert(
                stream, stream_info=StreamInfo(extension=ext, mimetype=mime_type)
            )
            return result.markdown

        # Plain text: wrap in code block or return as-is
        if isinstance(content, bytes):
            raw = content
            encodings = ('utf-8', 'utf-8-sig', 'cp1252', 'latin-1', 'iso-8859-1')
            for encoding in encodings:
                try:
                    content = raw.decode(encoding)
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            else:
                content = raw.decode('utf-8', errors='replace')
        return f"```\n{content}\n```" if mime_type == 'text/plain' else content

    def collect_files(self):
        """
        Read all files in the folder, convert their contents to markdown, and store them in the collection.
        """
        files = self.list_files()
        for file in files:
            raw = self.read_file_raw(file['id'])
            md_content = self.convert_to_markdown(raw, file['mimeType'], file['name'])
            self.entire_knowledge_base += md_content
            self.entire_knowledge_base += "\n\n"
            base = os.path.splitext(file['name'])[0]
            self.collection[f"{base}.md"] = md_content
        # How many characters in all the documents?
        print(f"Total characters in knowledge base: {len(self.entire_knowledge_base):,}")

    def get_collection(self) -> Dict[str, str]:
        """
        Get the collection of markdown-formatted file contents.
        Returns:
            Dict[str, str]: Dictionary mapping file names to markdown contents.
        """
        return self.collection

# Example usage:
# collector = GoogleDriveMarkdownCollector('path/to/credentials.json', 'your_folder_id')
# collector.collect_files()
# collection = collector.get_collection()
# print(collection)
