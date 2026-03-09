import os
from typing import List, Dict
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import io

class GoogleDriveClient:
    """
    A class to read files from a Google Drive directory, convert their contents to markdown,
    and store them as a collection for later use.
    """
    def __init__(self, credentials_path: str, folder_id: str):
        """
        Initialize the collector with Google service account credentials and folder ID.
        Args:
            credentials_path (str): Path to the Google service account credentials JSON file.
            folder_id (str): Google Drive folder ID to read files from.
        """
        self.credentials_path = credentials_path
        self.folder_id = folder_id
        self.service = self._authenticate()
        self.collection = {}

    def _authenticate(self):
        """
        Authenticate with Google Drive API using service account credentials.
        Returns:
            googleapiclient.discovery.Resource: Authenticated Drive API service.
        """
        creds = service_account.Credentials.from_service_account_file(
            self.credentials_path,
            scopes=['https://www.googleapis.com/auth/drive']
        )
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

    def read_file(self, file_id: str) -> str:
        """
        Read the contents of a file from Google Drive.
        Args:
            file_id (str): The ID of the file to read.
        Returns:
            str: The file contents as a string.
        """
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read().decode('utf-8')

    def convert_to_markdown(self, content: str, mime_type: str) -> str:
        """
        Convert file content to markdown format.
        Args:
            content (str): The file content.
            mime_type (str): The MIME type of the file.
        Returns:
            str: Markdown-formatted content.
        """
        # Simple conversion: if plain text, wrap in markdown code block
        if mime_type == 'text/plain':
            return f"```\n{content}\n```"
        # For other types, extend as needed
        return content

    def collect_files(self):
        """
        Read all files in the folder, convert their contents to markdown, and store them in the collection.
        """
        files = self.list_files()
        for file in files:
            content = self.read_file(file['id'])
            md_content = self.convert_to_markdown(content, file['mimeType'])
            self.collection[file['name']] = md_content

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
