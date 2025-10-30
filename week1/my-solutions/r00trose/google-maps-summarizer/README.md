# Google Maps Review Summarizer - Day 2 Project

AI-powered Google Maps review analyzer that scrapes **REAL reviews** and analyzes them using Llama 3.2 via Ollama.

## 🎯 Overview

This project demonstrates web scraping and LLM-based analysis by extracting real Google Maps reviews and generating AI-powered insights using Llama 3.2.

## ✨ Features

- **Real Web Scraping**: Extracts actual reviews from any Google Maps location using Playwright
- **Async Operations**: Efficient asynchronous scraping and data processing
- **Smart Scrolling**: Automatically loads more reviews by scrolling
- **AI Analysis**: Comprehensive sentiment analysis, key themes, pros/cons, and summary
- **Customizable**: Analyze 10-50 reviews per location
- **Local LLM**: Uses Llama 3.2 via Ollama - no API costs!
- **Error Handling**: Robust timeout and error recovery mechanisms

## 📋 Prerequisites

- Python 3.8+
- Google Chrome browser (installed automatically by Playwright)
- Ollama with Llama 3.2: `ollama pull llama3.2`

## 🚀 Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Playwright browser
```bash
playwright install chromium
```

### 3. Ensure Ollama is running
```bash
ollama serve
```

## 💡 Usage

### Run the analyzer
```bash
python google_maps_summarizer.py
```

### Example session
```
🗺️  Google Maps Review Summarizer (REAL Reviews)
    Powered by Llama 3.2 via Ollama

🔗 Enter Google Maps URL: https://www.google.com/maps/place/...
📊 How many reviews to analyze? (default: 20): 15

🌐 Launching browser...
📜 Scrolling to load reviews...
✅ Successfully scraped 15 reviews!

📝 Sample of REAL Reviews:
⭐⭐⭐⭐⭐
Beautiful architecture! The blue tiles are stunning...

🧠 Analyzing reviews with Llama 3.2...

📊 ANALYSIS OF REAL REVIEWS
1. **Overall Sentiment**: Positive
2. **Key Themes**: Architecture, History, Atmosphere
3. **Pros**: [actual insights from real reviews]
...
```

## 🛠️ Technologies Used

- **Playwright**: Modern web automation for reliable scraping
- **Async Python**: Efficient asynchronous operations
- **Ollama**: Local LLM runtime
- **Llama 3.2**: Meta's language model for analysis
- **Python 3.8+**: Core implementation

## 🎓 What I Learned

### Day 2 Concepts Applied:
- **Web Scraping with Playwright**: Extracting dynamic content from modern websites
- **Async Programming**: Using `asyncio` for efficient I/O operations
- **DOM Navigation**: Finding and extracting specific HTML elements
- **Timeout Handling**: Managing slow-loading content gracefully
- **LLM Integration**: Using Llama 3.2 via Ollama for sentiment analysis
- **Prompt Engineering**: Crafting effective prompts for structured analysis
- **Data Processing**: Cleaning and structuring scraped data
- **Error Recovery**: Building robust scrapers with proper exception handling

## 🐛 Troubleshooting

### "Could not extract reviews"
- Make sure the URL is a Google Maps **place page** (not search results)
- Some places may have reviews disabled
- Try a different, popular location

### Browser doesn't open
- Chromium will be downloaded automatically on first run
- Make sure you ran: `playwright install chromium`

### Ollama connection error
- Ensure Ollama is running: `ollama serve`
- Verify llama3.2 is installed: `ollama list`

### Scraping is slow
- Normal! Playwright waits for page loads and elements
- Scraping 20 reviews typically takes 30-60 seconds
- Be patient, don't interrupt the process

## ⚠️ Important Notes

- **Educational Use**: This project is for learning purposes only
- **Rate Limiting**: Don't scrape too aggressively
- **Terms of Service**: Be aware that web scraping may violate Google's ToS
- **Reliability**: Scraping may break if Google changes their HTML structure

## 🚀 Future Enhancements

- [ ] Export results to JSON/CSV/Markdown
- [ ] Visualize rating distribution with charts
- [ ] Compare multiple locations side-by-side
- [ ] Track reviews over time
- [ ] Detect suspicious/fake reviews
- [ ] Generate suggested responses to negative reviews
- [ ] Batch process multiple locations

## 📄 License

MIT License - free to use for learning purposes.

## 👤 Author

İrem Bezci (r00trose)  
LLM Engineering Course - Week 1, Day 2 Assignment

## 🙏 Acknowledgments

- **Ed Donner** - Course instructor
- **Ollama** - Local LLM framework
- **Meta** - Llama 3.2 model
- **Playwright** - Modern web automation library
- **Microsoft** - Playwright development