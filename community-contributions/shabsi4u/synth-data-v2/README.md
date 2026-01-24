# Synthetic Data Generator v2

Business-grade synthetic data generation using LLMs with support for multiple backends.

## Features

- Generate synthetic data from JSON schemas
- Support for HuggingFace Inference API
- SQLite database for generation history
- Multiple export formats (CSV, JSON, JSONL)
- Streaming exports for large datasets
- Export metadata tracking
- Professional Streamlit UI (coming in Step 6)
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

### Using the Python API

```python
from synth_data.backends import HuggingFaceAPIBackend
from synth_data.services import GeneratorService, ExportService, ExportFormat

# Initialize services
backend = HuggingFaceAPIBackend(api_key="hf_xxx")
gen_service = GeneratorService(backend, save_to_db=True)
export_service = ExportService()

# Define schema
schema = {
    "name": {"type": "string"},
    "age": {"type": "integer"},
    "email": {"type": "string"}
}

# Generate data
result = gen_service.generate(schema, num_records=100)

# Export to different formats
export_service.export_to_file(result["data"], "output.csv", ExportFormat.CSV)
export_service.export_to_file(result["data"], "output.json", ExportFormat.JSON, pretty=True)
export_service.export_to_file(result["data"], "output.jsonl", ExportFormat.JSONL)
```

### Using the Streamlit UI (Coming in Step 6)

1. Open the Streamlit app in your browser
2. Enter your HuggingFace API key (or configure in .env)
3. Define your data schema in JSON format
4. Specify the number of records to generate
5. Click "Generate" and wait for results
6. Download your data in CSV, JSON, or JSONL format
7. View generation history

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

## Implementation Progress

This project is being built incrementally following the plan in `PLAN.md`.

**Phase 1: Foundation & MVP**

- ✅ Step 1: Project structure and dependencies
- ✅ Step 2: ModelBackend interface (abstract base class)
- ✅ Step 3: HuggingFaceAPIBackend + Database layer
- ✅ Step 4: GeneratorService orchestration layer
- ✅ Step 5: ExportService (CSV, JSON, JSONL, streaming)
- ⏳ Step 6: Streamlit UI (next)

**Future Phases:**
- Phase 2: Local quantized models, Ollama, batch processing, quality metrics
- Phase 3: Multi-page UI, quality visualizations, template system
- Phase 4: HuggingFace Spaces deployment, multi-model comparison

See `STEP_4_GENERATION_SERVICE.md` and `STEP_5_EXPORT_SERVICE.md` for detailed documentation.

## Running Demos

```bash
# Demo the generation service
uv run python demo_generator.py

# Demo the export service
uv run python demo_export.py
```

## License

MIT
