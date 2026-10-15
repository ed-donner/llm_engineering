# Website Brochure Generator

An AI-powered tool that automatically generates professional brochures from any website using Large Language Models (LLMs). Built with a clean hybrid architecture combining classes and functions for optimal performance and maintainability.

## Features

- 🤖 **Multi-LLM Support**: Works with OpenAI, Anthropic Claude, and Google Gemini
- 🌐 **Smart Web Scraping**: Automatically extracts relevant content and links
- 📄 **Professional Brochures**: Generates well-structured markdown brochures
- 🎨 **Beautiful UI**: Clean Gradio interface for easy interaction
- ⚡ **Streaming Output**: Real-time brochure generation
- 🔧 **Robust Error Handling**: Comprehensive error management and validation

## Architecture

The project uses a hybrid approach combining the best of object-oriented and functional programming:

### Classes (Stateful Components)
- **`LLMInterface`**: Manages API clients and LLM interactions
- **`BrochureUI`**: Handles Gradio interface and user interactions

### Functions (Stateless Operations)
- **`scrape_website()`**: Pure function for web scraping
- **`get_relevant_links()`**: Analyzes links for brochure relevance
- **`generate_brochure_stream()`**: Orchestrates brochure generation workflow

## Installation

### Option 1: Using pip
```bash
pip install -r requirements.txt
```

### Option 2: Using poetry (recommended)
```bash
poetry install
```

### Option 3: Development setup
```bash
pip install -e ".[dev]"
```

## Configuration

Create a `.env` file in the project root with your API keys:

```env
# OpenAI API Key (starts with sk-proj-)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Key (starts with sk-ant-)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here
```

## Usage

### Command Line
```bash
python website_brochure_generator.py
```

### Programmatic Usage
```python
from website_brochure_generator import create_brochure_app

# Create the app
app = create_brochure_app()

# Launch with custom settings
app.launch(
    share=True,
    server_name="0.0.0.0",
    server_port=7860
)
```

### Direct Function Usage
```python
from website_brochure_generator import scrape_website, LLMInterface, generate_brochure_stream

# Scrape a website
website_data = scrape_website("https://example.com")

# Initialize LLM
llm = LLMInterface("openai")

# Generate brochure
for chunk in generate_brochure_stream(website_data, llm):
    print(chunk, end="")
```

## Supported Models

| Provider | Model | API Key Format |
|----------|-------|----------------|
| OpenAI | GPT-4o Mini | `sk-proj-...` |
| Anthropic | Claude 3.5 Sonnet | `sk-ant-...` |
| Google | Gemini 2.0 Flash | Any valid key |

## How It Works

1. **Website Scraping**: Extracts content, links, and metadata from the target website
2. **Link Analysis**: Uses LLM to identify relevant pages (About, Careers, Products, etc.)
3. **Content Aggregation**: Scrapes additional relevant pages
4. **Brochure Generation**: Creates a structured markdown brochure using AI
5. **Streaming Output**: Displays results in real-time through the UI

## Project Structure

```
Website_brochure_generator_with_UI/
├── website_brochure_generator.py  # Main application
├── prompts.py                     # Prompt templates and configurations
├── pyproject.toml                 # Project configuration
├── requirements.txt               # Dependencies
├── README.md                      # This file
├── env.example                    # Environment variables template
└── .env                          # API keys (create this)
```

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black website_brochure_generator.py
```

### Type Checking
```bash
mypy website_brochure_generator.py
```

### Linting
```bash
flake8 website_brochure_generator.py
```

## API Reference

### Core Functions

#### `scrape_website(url: str) -> Dict`
Scrapes a website and returns structured data including title, content, and links.

#### `validate_url(url: str) -> bool`
Validates if a URL is properly formatted.

#### `get_relevant_links(website_data: Dict, llm_interface: LLMInterface) -> List[Dict]`
Uses LLM to analyze and filter relevant links for brochure generation.

#### `generate_brochure_stream(website_data: Dict, llm_interface: LLMInterface) -> Generator[str, None, None]`
Generates brochure content by streaming from the LLM.

### Classes

#### `LLMInterface(model_name: str)`
Manages LLM API interactions with stateful client management.

**Methods:**
- `query_stream(user_prompt: str, system_prompt: str) -> Generator[str, None, None]`
- `query_json(user_prompt: str, system_prompt: str) -> Dict`

#### `BrochureUI()`
Gradio interface for the brochure generator.

**Methods:**
- `generate_brochure_ui(model: str, url: str) -> str`
- `launch(**kwargs)`

## Error Handling

The application includes comprehensive error handling for:
- Invalid URLs
- Network connectivity issues
- API key validation
- LLM response errors
- Web scraping failures

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure your API keys are correctly set in the `.env` file
2. **Network Errors**: Check your internet connection and firewall settings
3. **Import Errors**: Make sure all dependencies are installed via `pip install -r requirements.txt`

### Getting Help

- Check the logs for detailed error messages
- Ensure all required dependencies are installed
- Verify your API keys are valid and have sufficient credits

## Roadmap

- [ ] Add support for more LLM providers
- [ ] Implement caching for better performance
- [ ] Add custom brochure templates
- [ ] Support for multiple languages
- [ ] Batch processing capabilities
- [ ] API endpoint for programmatic access
