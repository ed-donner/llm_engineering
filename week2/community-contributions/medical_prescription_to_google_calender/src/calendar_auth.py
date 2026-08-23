import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build  # Add this import

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

def authenticate_google_calender():
    creds = None
    token_path = r"C:\Users\Legion\Desktop\projects\medical_prescription_to_google_calender\token.json"

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(r"C:\Users\Legion\Desktop\projects\medical_prescription_to_google_calender\credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    # Build and return the service instead of just credentials
    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building service: {e}")
        return None

if __name__ == "__main__":
    authenticate_google_calender()