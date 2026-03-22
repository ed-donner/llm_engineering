# PrettyPage Generator

Transform any text into a beautiful, responsive webpage.

## What it does

Paste your text (notes, articles, documentation, etc.) and get a styled, single-page website using your exact words. Choose from different themes like Minimal, Professional, Colorful, or Modern Gradient.

## Requirements

- Python 3.8+
- OpenAI API key
- Google API key (optional, for Gemini)

## Setup

1. Install dependencies:
```bash
pip install gradio openai python-dotenv
```

2. Create a `.env` file:
```
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here
```

3. Run the app:
```bash
python text_to_html.py 
```

4. Open the link in your browser 

## Usage

1. Paste your text in the input box
2. Choose a model (GPT-4o-mini or Gemini-Flash)
3. Select a style theme
4. Click "Generate Page"
5. Copy the HTML and save as `index.html`