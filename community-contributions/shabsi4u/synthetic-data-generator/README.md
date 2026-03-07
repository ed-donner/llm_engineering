# Cursor Synth - Synthetic Data Generator

A comprehensive synthetic data generation toolkit with two deployment options: **local/Colab notebook** for open-source models and **Python app** for cloud inference.

## 🚀 Quick Start

### Option 1: Python App (Recommended)
**Best for**: Production use, cloud inference, Hugging Face models

```bash
# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Add your HF_API_KEY to .env

# Run the Gradio UI
uv run gradio_ui.py
```

### Option 2: Jupyter Notebook
**Best for**: Experimentation, local models, Colab deployment

Open `synthetic_data_generator_colab.ipynb` in:
- **Google Colab** (recommended for free GPU access)
- **Local Jupyter** (requires local model setup)

## 📋 Project Overview

### 🐍 Python App (`gradio_ui.py`)
**Cloud-based inference using Hugging Face Inference API**

**Features:**
- ✅ **Lightweight**: No local model downloads (saves GB of space)
- ✅ **Fast startup**: No model loading time
- ✅ **Always up-to-date**: Uses latest model versions
- ✅ **Scalable**: Handles multiple concurrent requests
- ✅ **Easy deployment**: Works anywhere with internet

**Supported Models:**
- SmolLM3-3B (default)
- Any model available on Hugging Face Inference API
- Easy model switching via configuration

**Dependencies:**
```toml
dependencies = [
  "gradio>=4.0.0",
  "openai>=1.0.0",      # For Hugging Face router
  "python-dotenv>=1.0.0",
  "jsonschema>=4.19.0",
  "pytest>=7.0.0"
]
```

### 📓 Jupyter Notebook (`synthetic_data_generator_colab.ipynb`)
**Local model inference for experimentation**

**Features:**
- ✅ **Full control**: Run any open-source model locally
- ✅ **No API costs**: Free to use (except compute)
- ✅ **Privacy**: Data never leaves your machine
- ✅ **Customization**: Modify models, prompts, parameters
- ✅ **Colab ready**: Works on Google Colab with free GPU

**Supported Models:**
- Any Hugging Face model (via transformers)
- Custom fine-tuned models
- Local model files

## 🎯 Use Cases

### Choose Python App When:
- Building production applications
- Need fast, reliable inference
- Want to avoid model management
- Deploying to cloud platforms
- Working with team members

### Choose Notebook When:
- Experimenting with new models
- Need full control over inference
- Working with sensitive data
- Learning about model internals
- Custom model fine-tuning

## 🛠️ Technical Architecture

### Python App Stack
```
Gradio UI → Generator → HFClient → Hugging Face Inference API
                ↓
         TemplateRegistry + Validator
```

### Notebook Stack
```
Jupyter → Local Model Loading → Transformers → GPU/CPU Inference
                ↓
         Custom Prompting + Validation
```

## 📊 Data Templates

Both implementations support the same data generation templates:

- **👤 User Profiles**: Names, emails, demographics
- **🏢 Job Descriptions**: Roles, requirements, responsibilities  
- **📦 Product Specs**: Names, categories, features, pricing
- **📍 Addresses**: Street, city, state, postal codes
- **🔧 Custom**: Define your own schemas and prompts with intelligent few-shot examples

## 🚀 Getting Started

### For Python App:
1. Clone the repository
2. Run `uv sync` to install dependencies
3. Set up your `.env` file with `HF_API_KEY`
4. Run `uv run gradio_ui.py`
5. Open http://localhost:7860

### For Notebook:
1. Open `synthetic_data_generator_colab.ipynb`
2. Run all cells in Google Colab
3. Or install locally: `pip install transformers torch`

## 🔧 Custom Prompts

The Python app supports intelligent custom prompts with automatic few-shot examples:

### **Features:**
- ✅ **Smart Examples**: Automatically generates relevant few-shot examples
- ✅ **Count Detection**: Understands count from your prompt ("Generate 3 items...")
- ✅ **Anti-Thinking**: Prevents model from using `<think>` tags
- ✅ **JSON Format**: Ensures proper JSON array output
- ✅ **Tone Support**: Applies your specified tone to generated content

### **Example Custom Prompts:**
```
Generate 3 social media posts as JSON array. Each post should have: platform, content, hashtags (array), engagement_metrics (likes, shares, comments). Tone: engaging and modern.
```

```
Create 5 customer reviews as JSON array. Each review needs: rating (1-5), text, author, date, product_name. Tone: authentic and detailed.
```

### **How It Works:**
1. **Select "custom"** from the Template dropdown
2. **Enter your prompt** in the Custom prompt field
3. **Set tone** (optional, defaults to "concise")
4. **Click Generate** - the system automatically:
   - Adds a relevant few-shot example
   - Extracts count from your prompt
   - Applies anti-thinking instructions
   - Generates proper JSON arrays

## 🔧 Configuration

### Environment Variables
```bash
HF_API_KEY=your_huggingface_token_here
PORT=7860  # Optional, defaults to 7860
```

### Model Configuration
```python
# In gradio_ui.py
HF_MODEL_ID = "HuggingFaceTB/SmolLM3-3B:hf-inference"
```

## 🧪 Testing

```bash
# Run tests
uv run pytest -q

# Run with verbose output
uv run pytest -v
```

## 📈 Performance

### Python App (Cloud Inference)
- **Startup time**: ~2-3 seconds
- **Memory usage**: ~50MB
- **Inference latency**: 1-3 seconds
- **Throughput**: Limited by API rate limits
- **Custom prompts**: Intelligent few-shot examples, count detection, anti-thinking

### Notebook (Local Inference)
- **Startup time**: 30-60 seconds (model loading)
- **Memory usage**: 2-8GB (depending on model)
- **Inference latency**: 0.5-2 seconds
- **Throughput**: Limited by local hardware

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.
