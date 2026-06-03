# Website Brochure Generator

An AI-powered tool that automatically generates professional brochures from any website. The tool analyzes website content, extracts relevant information, and creates beautifully formatted brochures using OpenAI's GPT models.

## Features

- 🌐 **Website Analysis**: Automatically scrapes and analyzes website content
- 🤖 **AI-Powered**: Uses OpenAI GPT-4o-mini for intelligent content generation
- 📄 **Professional Output**: Generates markdown-formatted brochures
- 🌍 **Multi-Language Support**: Translate brochures to any language using AI
- 🎨 **Beautiful Output**: Rich terminal formatting and native Jupyter markdown rendering
- ⚡ **Streaming Support**: Real-time brochure generation with live updates
- 🖥️ **Multiple Interfaces**: Command-line script and interactive Jupyter notebook
- 📓 **Interactive Notebook**: Step-by-step execution with widgets and examples

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Jupyter notebook environment (for notebook usage)

## Installation

### Option 1: Using uv (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone or download the project
cd Website_brochure_generator

# Install dependencies with uv
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Option 2: Using pip

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 3: Using pip with pyproject.toml

```bash
# Install in development mode
pip install -e .

# Or install with optional dev dependencies
pip install -e ".[dev]"
```

## Setup

1. **Get your OpenAI API key**:
   - Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
   - Create a new API key

2. **Set up environment variables**:
   Create a `.env` file in the project directory:
   ```bash
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

### Option 1: Jupyter Notebook (Recommended for Interactive Use)

1. **Open the notebook**:
   ```bash
   jupyter notebook website_brochure_generator.ipynb
   ```

2. **Run the cells step by step**:
   - Configure your API key
   - Try the interactive examples
   - Use the widget interface for easy brochure generation

3. **Features in the notebook**:
   - Interactive widgets for URL input and options
   - Step-by-step examples with explanations
   - Custom functions for advanced usage
   - Save brochures to files
   - Multiple language translation examples
   - Quick website analysis tools
   - Custom brochure generation with focus areas
   - Comprehensive troubleshooting guide

### Option 2: Command Line Interface

```bash
# Basic usage
python website_brochure_generator.py https://example.com

# The tool will prompt you to choose:
# 1. Display mode: Complete output OR Stream output
# 2. Translation: No translation OR Translate to another language
```

### Option 3: Python Script

```python
from website_brochure_generator import create_brochure, stream_brochure, translate_brochure

# Create a complete brochure
result = create_brochure("https://example.com")

# Stream brochure generation in real-time
result = stream_brochure("https://example.com")

# Translate brochure to Spanish (complete output)
spanish_brochure = translate_brochure("https://example.com", "Spanish", stream_mode=False)

# Translate brochure to French (streaming output)
french_brochure = translate_brochure("https://example.com", "French", stream_mode=True)
```

### Programmatic Usage

```python
from website_brochure_generator import Website, get_links, create_brochure, translate_brochure

# Analyze a website
website = Website("https://example.com")
print(f"Title: {website.title}")

# Get relevant links
links = get_links("https://example.com")
print(f"Found {len(links['links'])} relevant pages")

# Generate brochure
brochure = create_brochure("https://example.com")

# Translate brochure to multiple languages (complete output)
spanish_brochure = translate_brochure("https://example.com", "Spanish", stream_mode=False)
german_brochure = translate_brochure("https://example.com", "German", stream_mode=False)

# Translate brochure with streaming output
chinese_brochure = translate_brochure("https://example.com", "Chinese", stream_mode=True)
```

## How It Works

1. **Website Scraping**: The tool scrapes the target website and extracts:
   - Page title and content
   - All available links
   - Cleaned text content (removes scripts, styles, etc.)

2. **Link Analysis**: Uses AI to identify relevant pages for the brochure:
   - About pages
   - Company information
   - Careers/Jobs pages
   - News/Blog pages

3. **Content Aggregation**: Scrapes additional relevant pages and combines all content

4. **Brochure Generation**: Uses OpenAI GPT-4o-mini to create a professional brochure including:
   - Company overview
   - Services/Products
   - Company culture
   - Career opportunities
   - Contact information

5. **Translation (Optional)**: If translation is requested, uses AI to translate the brochure to the target language while:
   - Maintaining markdown formatting
   - Preserving professional tone
   - Keeping proper nouns and company names intact
   - Ensuring natural, fluent translation

## Output

The tool generates markdown-formatted brochures that include:

- **Company Overview**: Summary of the business
- **Services/Products**: What the company offers
- **Company Culture**: Values and work environment
- **Career Opportunities**: Job openings and company benefits
- **Contact Information**: How to reach the company

## Dependencies

### Core Dependencies
- `openai>=1.0.0` - OpenAI API client
- `python-dotenv>=1.0.0` - Environment variable management
- `requests>=2.25.0` - HTTP requests for web scraping
- `beautifulsoup4>=4.9.0` - HTML parsing
- `rich>=13.0.0` - Beautiful terminal output (for command-line usage)
- `ipywidgets>=8.0.0` - Interactive widgets (for Jupyter notebook)

## Development

### Setting up development environment

```bash
# Install with dev dependencies
uv sync --extra dev
# or
pip install -e ".[dev]"
```

### Running tests

```bash
pytest
```

### Code formatting

```bash
black website_brochure_generator.py
```

### Type checking

```bash
mypy website_brochure_generator.py
```

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'rich'**
   - Make sure you've installed all dependencies: `pip install -r requirements.txt`

2. **OpenAI API Key Error**
   - Verify your API key is set in the `.env` file
   - Check that your API key has sufficient credits

3. **Website Scraping Issues**
   - Some websites may block automated requests
   - The tool uses a standard User-Agent header to avoid basic blocking

4. **Display Issues**
   - For command-line: Make sure Rich is properly installed: `pip install rich`
   - For Jupyter: Make sure ipywidgets is installed: `pip install ipywidgets`
   - Some terminals may not support all Rich features

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions, please open an issue on the project repository.
