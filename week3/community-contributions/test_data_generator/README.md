---
title: AI Powered Test Data Generator
emoji: 🧪
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: "4.31.0"
app_file: app.py
pinned: false
---

# AI-Powered Test Data Generator

Generate realistic test data for testing, development, and prototyping using open-source LLMs via HuggingFace Inference API.

## Features

- Generate structured data (users, products, orders, employees, transactions, reviews)
- Custom schema support with JSON definitions
- Multiple export formats (CSV, JSON)
- Uses HuggingFace Inference API with open-source models
- Batch generation (up to 100 records)
- Multiple locale support
- Deployable on HuggingFace Spaces

## Available Models

- `meta-llama/Meta-Llama-3.1-8B-Instruct`
- `Qwen/Qwen2.5-72B-Instruct`
- `google/gemma-2-9b-it`

## Setup

### Local Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/test-data-generator.git
cd test-data-generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your HuggingFace token:
```bash
export HF_TOKEN=your_token_here
```

4. Run the app:
```bash
python app.py
```

### HuggingFace Spaces Deployment

1. Create a new Space at [huggingface.co/spaces](https://huggingface.co/spaces)
2. Select "Gradio" as the SDK
3. Upload `app.py` and `requirements.txt`
4. Add `HF_TOKEN` as a Space secret (Settings > Repository secrets)

## Usage

### Template Generator

1. Select an LLM model from the dropdown
2. Choose a data type template (Users, Products, Orders, etc.)
3. Customize fields if needed
4. Set the number of records to generate
5. Add custom instructions (optional)
6. Click "Generate Data"
7. Download as CSV or JSON

### Custom Schema

Define your own schema as a JSON object where:
- Each key is a field name
- Each value describes what data to generate

Example:
```json
{
    "id": "unique integer identifier",
    "company_name": "realistic company name",
    "industry": "industry sector",
    "revenue": "annual revenue in millions USD",
    "employees": "number of employees",
    "founded_year": "year company was founded"
}
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `HF_TOKEN` | HuggingFace API token | Recommended |

Get your free token at: https://huggingface.co/settings/tokens

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
