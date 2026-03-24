import os
import pickle
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate():
    """Authenticate and return Drive service."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

def list_files(service, folder_id):
    """Recursively list all PDF and text files in a folder."""
    file_list = []
    query = f"'{folder_id}' in parents and trashed = false"
    page_token = None
    while True:
        response = service.files().list(
            q=query,
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType)',
            pageToken=page_token
        ).execute()
        for file in response.get('files', []):
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                file_list.extend(list_files(service, file['id']))
            elif file['mimeType'] in ['application/pdf', 'text/plain'] or file['name'].endswith('.txt'):
                file_list.append(file)
        page_token = response.get('nextPageToken', None)
        if not page_token:
            break
    return file_list

def download_file(service, file_id, file_name, destination_folder):
    """Download a file only if it does not already exist."""
    os.makedirs(destination_folder, exist_ok=True)
    file_path = os.path.join(destination_folder, file_name)

    # Handle name collisions by adding a suffix
    base, ext = os.path.splitext(file_name)
    counter = 1
    original_path = file_path
    while os.path.exists(file_path):
        file_path = os.path.join(destination_folder, f"{base}_{counter}{ext}")
        counter += 1

    # If the final path already exists (from a previous run), skip download
    if os.path.exists(file_path):
        print(f"File already exists, skipping: {file_path}")
        return file_path

    request = service.files().get_media(fileId=file_id)
    with io.FileIO(file_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Downloading {file_name}: {int(status.progress() * 100)}%")
    return file_path