# Web Scraper & Data Analyzer

A modern Python application with a sleek PyQt5 GUI for web scraping, data analysis, visualization, and AI-powered website insights. Features a clean, minimalistic design with real-time progress tracking, comprehensive data filtering, and an integrated AI chat assistant for advanced analysis.

## Features

- **Modern UI**: Clean, minimalistic design with dark theme and smooth animations
- **Web Scraping**: Multi-threaded scraping with configurable depth (max 100 levels)
- **Data Visualization**: Interactive table with sorting and filtering capabilities
- **Content Preview**: Dual preview system with both text and visual HTML rendering
- **Data Analysis**: Comprehensive statistics and domain breakdown
- **AI-Powered Analysis**: Chat-based assistant for website insights, SEO suggestions, and content analysis
- **Export Functionality**: JSON export with full metadata
- **URL Normalization**: Handles www/non-www domains intelligently
- **Real-time Progress**: Live progress updates during scraping operations
- **Loop Prevention**: Advanced duplicate detection to prevent infinite loops
- **Smart Limits**: Configurable limits to prevent runaway scraping

## AI Analysis Tab

The application features an advanced **AI Analysis** tab:

- **Conversational Chat UI**: Ask questions about your scraped websites in a modern chat interface (like ChatGPT)
- **Quick Actions**: One-click questions for structure, SEO, content themes, and performance
- **Markdown Responses**: AI replies are formatted for clarity and readability
- **Context Awareness**: AI uses your scraped data for tailored insights
- **Requirements**: Internet connection and the `openai` Python package (see Installation)
- **Fallback**: If `openai` is not installed, a placeholder response is shown

## Loop Prevention & Duplicate Detection

The scraper includes robust protection against infinite loops and circular references:

### 🔄 URL Normalization
- Removes `www.` prefixes for consistent domain handling
- Strips URL fragments (`#section`) to prevent duplicate content
- Removes trailing slashes for consistency
- Normalizes query parameters

### 🚫 Duplicate Detection
- **Visited URL Tracking**: Maintains a set of all visited URLs
- **Unlimited Crawling**: No page limits per domain or total pages
- **Per-Page Duplicate Filtering**: Removes duplicate links within the same page

### 🛡️ Smart Restrictions
- **No Depth Limits**: Crawl as deep as the specified max_depth allows
- **Content Type Filtering**: Only scrapes HTML content
- **File Type Filtering**: Skips non-content files (PDFs, images, etc.)
- **Consecutive Empty Level Detection**: Stops if 3 consecutive levels have no new content

### 📊 Enhanced Tracking
- **Domain Page Counts**: Tracks pages scraped per domain (for statistics)
- **URL Check Counts**: Shows total URLs checked vs. pages scraped
- **Detailed Statistics**: Comprehensive reporting on scraping efficiency
- **Unlimited Processing**: No artificial limits on crawling scope

## Installation

1. **Clone or download the project files**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   - This will install all required packages, including `PyQt5`, `PyQtWebEngine` (for visual preview), and `openai` (for AI features).

3. **Run the application**:
   ```bash
   python web_scraper_app.py
   ```

## Usage

### 1. Scraping Configuration
- Enter a starting URL (with or without http/https)
- Set maximum crawl depth (1-100)
- Click "Start Scraping" to begin

### 2. Data View & Filtering
- View scraped data in an interactive table
- Filter by search terms or specific domains
- Double-click any row to preview content
- Export data to JSON format

### 3. Analysis & Statistics
- View comprehensive scraping statistics
- See domain breakdown and word counts
- Preview content in both text and visual formats
- Analyze load times and link counts
- Monitor duplicate detection efficiency

### 4. AI Analysis (New!)
- Switch to the **AI Analysis** tab
- Type your question or use quick action buttons (e.g., "Analyze the website structure", "Suggest SEO improvements")
- The AI will analyze your scraped data and provide actionable insights
- Requires an internet connection and the `openai` package

## Visual Preview Feature

The application includes a visual HTML preview feature that renders scraped web pages in a browser-like view:

- **Requirements**: PyQtWebEngine (automatically installed with requirements.txt)
- **Functionality**: Displays HTML content with proper styling and formatting
- **Fallback**: If PyQtWebEngine is not available, shows a text-only preview
- **Error Handling**: Graceful error messages for invalid HTML content

## Technical Details

- **Backend**: Pure Python with urllib and html.parser (no compilation required)
- **Frontend**: PyQt5 with custom modern styling
- **Threading**: Multi-threaded scraping for better performance
- **Data Storage**: Website objects with full metadata
- **URL Handling**: Intelligent normalization and domain filtering
- **Loop Prevention**: Multi-layered duplicate detection system
- **AI Integration**: Uses OpenAI API (via openrouter) for chat-based analysis

## File Structure

```
Testing/
├── web_scraper_app.py      # Main application (with AI and GUI)
├── module.py               # Core scraping logic
├── test.py                 # Basic functionality tests
├── requirements.txt        # Dependencies
└── README.md               # This file
```

## Troubleshooting

### Visual Preview Not Working
1. Ensure PyQtWebEngine is installed: `pip install PyQtWebEngine`
2. Check console output for import errors

### AI Analysis Not Working
1. Ensure the `openai` package is installed: `pip install openai`
2. Check your internet connection (AI requires online access)
3. If not installed, the AI tab will show a placeholder response

### Scraping Issues
1. Verify internet connection
2. Check URL format (add https:// if needed)
3. Try with a lower depth setting
4. Check console for error messages

### Loop Prevention
1. The scraper automatically prevents infinite loops
2. Check the analysis tab for detailed statistics
3. Monitor "Total URLs Checked" vs "Total Pages" for efficiency
4. Use lower depth settings for sites with many internal links

### Performance
- Use lower depth settings for faster scraping
- Filter data to focus on specific domains
- Close other applications to free up resources
- Monitor domain page counts to avoid hitting limits

## License

This project is open source and available under the MIT License. 