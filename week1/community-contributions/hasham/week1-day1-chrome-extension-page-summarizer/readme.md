# Webpage Summarizer Chrome Extension

A Chrome extension that uses OpenAI's API to summarize any webpage you're currently viewing.

## Setup Instructions

### 1. Get Your OpenAI API Key
- Go to https://platform.openai.com/api-keys
- Sign in or create an account
- Click "Create new secret key"
- Copy the key (starts with sk-...)

### 2. Configure the Extension
1. Copy `config.example.js` to `config.js`:
   ```
   cp config.example.js config.js
   ```
2. Open `config.js` and replace `'your-openai-api-key-here'` with your actual API key

### 3. Create Extension Icons (Optional)
You'll need 3 icon files (icon16.png, icon48.png, icon128.png).
You can:
- Create simple icons using any image editor
- Use a free icon from sites like flaticon.com
- Or temporarily use any square PNG images renamed appropriately

### 4. Load the Extension in Chrome
1. Open Chrome and go to: `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select your extension folder
5. The extension icon should appear in your toolbar

### 5. Use the Extension
1. Navigate to any webpage
2. Click the extension icon
3. Click "Summarize This Page"
4. Wait a few seconds for the AI-generated summary

## Features
- ✅ Summarizes any webpage content
- ✅ Uses OpenAI GPT-3.5-turbo
- ✅ Clean, simple interface
- ✅ Works on any website
- ✅ API key stored in separate config file (git-ignored for security)

## How It Works
1. Extracts text content from the current webpage
2. Sends it to OpenAI with a system prompt
3. Displays the generated summary in the popup

## Cost
Uses OpenAI API credits (very minimal cost per summary, typically < $0.01)

## Privacy & Security
- Your API key is stored in `config.js` which is git-ignored
- Never commit your `config.js` file to version control
- The API key stays on your local machine only

## For Developers
If you're contributing or forking this repo:
1. Copy `config.example.js` to `config.js`
2. Add your own OpenAI API key to `config.js`
3. The `.gitignore` file ensures `config.js` won't be committed