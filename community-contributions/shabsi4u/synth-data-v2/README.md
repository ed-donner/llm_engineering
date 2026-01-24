# Synthetic Data Generator v2

Business-grade synthetic data generation using LLMs with support for multiple backends.

## Features

- Generate synthetic data from JSON schemas
- Support for HuggingFace Inference API
- SQLite database for generation history
- Professional Streamlit UI
- CSV export functionality
- Secure API key management

## Quick Start

### Prerequisites

- Python 3.10+
- pip or uv

### Installation

```bash
# Clone repository (if needed)
cd synth-data-v2

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy environment template (optional - for local development)
cp .env.example .env

# Edit .env and add your API keys (optional)
nano .env
```

Note: API keys can also be provided via the Streamlit UI for hosted deployments.

### Run Application

```bash
# Start Streamlit app
streamlit run synth_data/ui/app.py
```

## Project Structure

```
synth_data/
├── backends/     # LLM backend implementations
├── database/     # SQLAlchemy models and services
├── services/     # Business logic (generation, export)
├── ui/           # Streamlit interface
└── utils/        # Helper functions
```

## Usage

1. Open the Streamlit app in your browser
2. Enter your HuggingFace API key (or configure in .env)
3. Define your data schema in JSON format
4. Specify the number of records to generate
5. Click "Generate" and wait for results
6. Download your data as CSV
7. View generation history in the expander

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black synth_data/
```

## Security

- Never commit API keys to git
- Use .env for local development (already in .gitignore)
- For hosted deployments, users provide keys via UI

## License

MIT
