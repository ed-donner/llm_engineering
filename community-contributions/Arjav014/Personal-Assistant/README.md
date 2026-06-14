# Personal AI Assistant with Google Calendar Integration

An interactive, Gradio-based personal assistant powered by the Groq API (using OpenAI SDK compatibility). The assistant features an autonomous agent loop that handles tool calling, specifically integrated with the **Google Calendar API** to schedule, list, and delete calendar events.

## Features
- **Persona**: An energetic, over-caffeinated best friend assistant who keeps answers extremely concise.
- **Dynamic Date Resolution**: Automatically retrieves the current date/time to parse relative time requests (like "tomorrow" or "next Friday").
- **Google Calendar Tools**:
  - List events for a specific day or upcoming week.
  - Create events with automated timezone offset alignment.
  - Delete events using Google Calendar event IDs.
- **Autonomous Tool-calling Loop**: Can handle multiple tool invocations in a single user turn.

---

## Prerequisites & Installation

### 1. Install Dependencies
Make sure you have a Python virtual environment set up, then install the required libraries:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root of the project (or ensure your environment has the following):
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Google Calendar API Setup
To allow the assistant to edit your Google Calendar:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable the **Google Calendar API**.
4. Configure the **OAuth Consent Screen**:
   - Set **User Type** to **External**.
   - Under **Test Users**, click **Add Users** and add the Google account email you wish to connect.
5. Generate credentials:
   - Go to **Credentials** -> **Create Credentials** -> **OAuth client ID**.
   - Select **Desktop app** as the application type.
   - Download the generated JSON file, rename it to `credentials.json`, and place it in this directory.

---

## Usage

1. Open `main.ipynb` in your Jupyter Notebook interface (VS Code, JupyterLab, etc.).
2. Run the cells in order.
3. When you run the interface and trigger a calendar action for the first time, a browser window will open automatically asking you to log in to your Google Account.
4. Once you approve the permissions, a `token.json` file will be created locally. Subsequent requests will run automatically without requiring browser interaction.

---

## Security Warning ⚠️

> [!WARNING]
> Do **NOT** commit `credentials.json` or `token.json` to public repositories (such as GitHub). They contain sensitive authentication credentials and refresh tokens for your Google Account.
> 
> These files are ignored by `.gitignore` in this project.
