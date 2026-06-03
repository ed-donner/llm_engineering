# AI Property Rental Assistant

An intelligent property rental assistant Jupyter notebook that scrapes real estate listings from OnTheMarket and uses a local LLM (DeepSeek R1) to analyze and recommend properties based on user requirements.

## Features

- **Web Scraping**: Automatically fetches property listings from OnTheMarket
- **AI-Powered Analysis**: Uses DeepSeek R1 model via Ollama for intelligent recommendations
- **Personalized Recommendations**: Filters and ranks properties based on:
  - Budget constraints
  - Number of bedrooms
  - Tenant type (student, family, professional)
  - Location preferences
- **Clean Output**: Returns formatted markdown with top 3-5 property recommendations
- **Smart Filtering**: Handles cases where no suitable properties are found with helpful suggestions

## Prerequisites

- Python 3.7+
- Ollama installed and running locally
- DeepSeek R1 14B model pulled in Ollama

## Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd property-rental-assistant
```

2. **Install required Python packages**
```bash
pip install requests beautifulsoup4 ollama ipython jupyter
```

3. **Install and setup Ollama**
```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# For Windows, download from: https://ollama.ai/download
```

4. **Pull the DeepSeek R1 model**
```bash
ollama pull deepseek-r1:14b
```

5. **Start Ollama server**
```bash
ollama serve
```

## Usage

### Running the Notebook

1. **Start Jupyter Notebook**
```bash
jupyter notebook
```

2. **Open the notebook**
Navigate to `property_rental_assistant.ipynb` in the Jupyter interface

3. **Run all cells**
Click `Cell` → `Run All` or use `Shift + Enter` to run cells individually

### Customizing Search Parameters

Modify the `user_needs` variable in the notebook:
```python
user_needs = "I'm a student looking for a 2-bedroom house in Durham under £2,000/month"
```

Other examples:
- `"Family of 4 looking for 3-bedroom house with garden in Durham, budget £2,500/month"`
- `"Professional couple seeking modern 1-bed apartment near city center, max £1,500/month"`
- `"Student group needs 4-bedroom house near Durham University, £600/month per person"`

### Changing the Property Website

Update the `website_url` variable in the notebook:
```python
website_url = "https://www.onthemarket.com/to-rent/property/durham/"
```

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   OnTheMarket   │────▶│  Web Scraper │────▶│   Ollama    │
│     Website     │     │  (BeautifulSoup)│    │ (DeepSeek R1)│
└─────────────────┘     └──────────────┘     └─────────────┘
                                                      │
                                                      ▼
                              ┌─────────────────────────────────┐
                              │   AI-Generated Recommendations  │
                              │   • Top 5 matching properties   │
                              │   • Filtered by requirements    │
                              │   • Markdown formatted output   │
                              └─────────────────────────────────┘
```

## Project Structure

```
property-rental-assistant/
│
├── property_rental_assistant.ipynb  # Main Jupyter notebook
└── README.md                         # This file
```

## 🔧 Configuration

### Ollama API Settings
```python
OLLAMA_API = "http://localhost:11434/api/chat"  # Default Ollama endpoint
MODEL = "deepseek-r1:14b"                        # Model to use
```

### Web Scraping Settings
```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
timeout = 10  # Request timeout in seconds
```

### Content Limits
```python
website.text[:4000]  # Truncate content to 4000 chars for token limits
```

## How It Works

1. **Web Scraping**: The `Website` class fetches and parses HTML content from the property listing URL
2. **Content Cleaning**: Removes scripts, styles, and images to extract clean text
3. **Prompt Engineering**: Combines system prompt with user requirements and scraped data
4. **LLM Analysis**: Sends the prompt to DeepSeek R1 via Ollama API
5. **Recommendation Generation**: The AI analyzes listings and returns top matches in markdown format

## 🛠️ Troubleshooting

### Ollama Connection Error
```
Error communicating with Ollama: [Errno 111] Connection refused
```
**Solution**: Ensure Ollama is running with `ollama serve`

### Model Not Found
```
Error: model 'deepseek-r1:14b' not found
```
**Solution**: Pull the model with `ollama pull deepseek-r1:14b`

### Web Scraping Blocked
```
Error fetching website: 403 Forbidden
```
**Solution**: The website may be blocking automated requests. Try:
- Updating the User-Agent string
- Adding delays between requests
- Using a proxy or VPN

### Insufficient Property Data
If recommendations are poor quality, the scraper may not be capturing listing details properly. Check:
- The website structure hasn't changed
- The content truncation limit (4000 chars) isn't too restrictive

## Future Enhancements

- [ ] Support multiple property websites (Rightmove, Zoopla, SpareRoom)
- [ ] Interactive CLI for dynamic user input
- [ ] Property image analysis
- [ ] Save search history and favorite properties
- [ ] Email notifications for new matching properties
- [ ] Price trend analysis
- [ ] Commute time calculations to specified locations
- [ ] Multi-language support
- [ ] Web interface with Flask/FastAPI
- [ ] Docker containerization

## Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM hosting
- [DeepSeek](https://www.deepseek.com/) for the R1 model
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for web scraping
- [OnTheMarket](https://www.onthemarket.com/) for property data
