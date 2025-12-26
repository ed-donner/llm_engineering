# 🏢 Company Brochure Generator - Chrome Extension

An AI-powered Chrome extension that generates professional company brochures from any website using OpenAI's GPT models.

## Features

- 🤖 AI-powered brochure generation using GPT-4o-mini
- 🌐 Extract information from company websites automatically
- 📋 Copy brochure to clipboard
- 💾 Download brochure as Markdown file
- ⚡ One-click form filling from current tab
- 🎨 Beautiful, modern UI

## Prerequisites

- Python 3.8 or higher
- Google Chrome browser
- OpenAI API key

## Installation

### 1. Set up the Backend Server

1. **Clone or navigate to the project directory:**
   ```powershell
   cd C:\work\ailearning\Myown\brochurechromeextension
   ```

2. **Create a virtual environment (if not already created):**
   ```powershell
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

4. **Install Python dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

5. **Create a `.env` file in the project root with your OpenAI API key:**
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

6. **Fix the `programsetup.py` file:**
   
   Update the model name from `"gpt-4.1-mini"` to `"gpt-4o-mini"` in both functions:
   - Line 10: Change `Model = "gpt-4.1-mini"` to `Model = "gpt-4o-mini"`
   - Line 49: Change `model="gpt-4.1-mini"` to `model="gpt-4o-mini"`

7. **Start the Flask server:**
   ```powershell
   python server.py
   ```

   You should see:
   ```
   OpenAI API key loaded successfully
   Starting Flask server on http://localhost:5000
   ```

### 2. Install the Chrome Extension

1. **Create extension icons (optional):**
   
   Create a folder called `icons` in the project directory and add icon images (16x16, 48x48, and 128x128 pixels) named `icon16.png`, `icon48.png`, and `icon128.png`. If you skip this step, Chrome will use default icons.

2. **Load the extension in Chrome:**
   
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in the top right)
   - Click "Load unpacked"
   - Select the project directory: `C:\work\ailearning\Myown\brochurechromeextension`

3. **Pin the extension:**
   
   Click the puzzle icon in Chrome's toolbar and pin the "Company Brochure Generator" extension for easy access.

## Usage

1. **Make sure the backend server is running:**
   ```powershell
   python server.py
   ```

2. **Click the extension icon** in your Chrome toolbar

3. **Enter company information:**
   - Company Name: e.g., "Hugging Face"
   - Company URL: e.g., "https://huggingface.co"
   
   OR
   
   - Click "Use Current Tab" to auto-fill from the current webpage

4. **Click "Generate Brochure"**
   
   The extension will:
   - Fetch the website content
   - Identify relevant company pages
   - Generate a professional brochure using AI
   - Display the result in the popup

5. **Use the generated brochure:**
   - Click "📋 Copy" to copy to clipboard
   - Click "💾 Download" to save as a Markdown file

## Project Structure

```
brochurechromeextension/
├── manifest.json           # Chrome extension configuration
├── popup.html             # Extension popup UI
├── popup.js               # Frontend JavaScript logic
├── popup.css              # Styling for the popup
├── background.js          # Service worker (background script)
├── server.py              # Flask backend API server
├── programsetup.py        # Brochure generation logic
├── commonfunctions.py     # Web scraping utilities
├── brochure.py            # Test script (original)
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
└── icons/                 # Extension icons (optional)
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

## How It Works

1. **User Input:** User enters company name and URL in the extension popup
2. **API Request:** Frontend sends POST request to Flask backend at `http://localhost:5000/generate-brochure`
3. **Web Scraping:** Backend fetches website content using BeautifulSoup
4. **AI Processing:** 
   - GPT-4o-mini identifies relevant company pages (About, Careers, etc.)
   - Fetches content from those pages
   - Generates a professional brochure in Markdown format
5. **Response:** Brochure is returned to the extension and displayed to the user

## Troubleshooting

### Extension doesn't load
- Make sure all files are in the correct directory
- Check Chrome's extension page for error messages
- Verify `manifest.json` is valid JSON

### "Failed to generate brochure" error
- Ensure the Flask server is running on `http://localhost:5000`
- Check the server terminal for error messages
- Verify your OpenAI API key is set in the `.env` file

### OpenAI API errors
- Check your API key is valid and has credits
- Verify the model name is `"gpt-4o-mini"` (not `"gpt-4.1-mini"`)
- Check your OpenAI account usage limits

### Import errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Verify the virtual environment is activated
- Check Python version is 3.8 or higher

## API Endpoints

### POST /generate-brochure
Generates a company brochure.

**Request:**
```json
{
  "company_name": "Hugging Face",
  "url": "https://huggingface.co"
}
```

**Response:**
```json
{
  "success": true,
  "brochure": "# Hugging Face\n\n...",
  "company_name": "Hugging Face",
  "url": "https://huggingface.co"
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "Brochure Generator API is running"
}
```

## Dependencies

### Python (Backend)
- `flask` - Web server framework
- `flask-cors` - CORS support for Chrome extension
- `beautifulsoup4` - Web scraping
- `requests` - HTTP requests
- `openai` - OpenAI API client
- `python-dotenv` - Environment variable management

### JavaScript (Frontend)
- No external dependencies - uses vanilla JavaScript

## License

This project is for educational purposes.

## Notes

- The extension requires an active internet connection
- OpenAI API calls may incur costs based on usage
- Generation time typically ranges from 30-60 seconds depending on website complexity
- The backend server must be running for the extension to work

## Future Enhancements

- [ ] Add support for different output formats (PDF, HTML)
- [ ] Implement caching to reduce API calls
- [ ] Add support for multiple AI models
- [ ] Include company logo extraction
- [ ] Add export to Google Docs/Word
- [ ] Implement batch processing for multiple companies
