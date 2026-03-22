## Setup Instructions

### Step 1: Install Dependencies

Run the cell below to install required packages.

### Step 2: Google Cloud Setup (IMPORTANT)

**You need to create OAuth credentials to access Gmail and Drive.**

#### Quick Navigation Guide:

1. **Create Project**: [Google Cloud Console](https://console.cloud.google.com) → Click project dropdown at top → "NEW PROJECT"

2. **Enable APIs**: 
   - ☰ Menu → APIs & Services → "+ ENABLE APIS AND SERVICES"
   - Search and enable: **Gmail API** and **Google Drive API**

3. **Configure OAuth Consent Screen** (Required first!):
   - ☰ Menu → APIs & Services → OAuth consent screen
   - Choose "External" → Fill in app name and your email
   - Add yourself as a **test user**

4. **Create Credentials**:
   - ☰ Menu → APIs & Services → Credentials
   - "+ CREATE CREDENTIALS" → "OAuth client ID"
   - Application type: "**Desktop app**"
   - Download the JSON file

5. **Save File**:
   - Rename downloaded file to `google_credentials.json`
   - Place in `week5/credentials/google_credentials.json`


**Folders created automatically:**
- `credentials/` - place your google_credentials.json here (you create this file)
- `tokens/` - authentication tokens (auto-created after first login)
- `vector_db_gmail_drive/` - vector database (auto-created)
