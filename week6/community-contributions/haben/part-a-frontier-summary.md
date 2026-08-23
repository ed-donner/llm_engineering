# Part A: Frontier Models - Implementation Summary

**Repository**: [ai-price-prediction-capstone](https://github.com/habeneyasu/ai-price-prediction-capstone)  
**Part**: Part A - Frontier Models (Week 6)  
**Status**: ✅ Completed  
**Branch**: `feat/w6-part-a-price-prediction`

---

## Overview

Part A implements a price prediction system that estimates product prices from textual descriptions using frontier language models. This component serves as the baseline for the three-part capstone project, establishing performance benchmarks that subsequent parts (fine-tuned models and autonomous agents) will be compared against.

The implementation leverages commercial frontier models through unified API interfaces, providing flexibility to test multiple models and providers without code modifications.

## Key Features

### 1. **Multi-Provider Model Support**
- **OpenRouter API Integration**: Unified interface providing access to multiple frontier models
  - Supports GPT-4, GPT-4o, GPT-4 Turbo variants
  - Supports Claude family models (Opus, Sonnet, Haiku)
  - Access to other commercial models available on OpenRouter platform
- **Ollama Local Inference**: Support for local model execution
  - Zero-cost inference for development and testing
  - Privacy-preserving option for sensitive data
  - Compatible with open-source models (LLaMA, Mistral, etc.) via Ollama CLI

### 2. **Evaluation Framework**
- **Metrics Implementation**:
  - Mean Absolute Error (MAE) - primary metric for price prediction
  - Mean Squared Error (MSE) - penalizes large errors
  - R² Score - variance explained by the model
  - Error distribution statistics
- **Visualization Components**:
  - Scatter plots comparing predicted vs actual prices
  - Error trend analysis with statistical confidence intervals
  - Color-coded error categorization (green/orange/red thresholds)
- **Performance Optimization**: Multi-threaded evaluation using ThreadPoolExecutor

### 3. **Configuration Management**
- Environment variable-based configuration (`.env` file)
- Model configuration options:
  - Provider selection (OpenRouter or Ollama)
  - Model identifier/version
  - Temperature parameter for generation
  - Maximum token output limit
- Evaluation configuration:
  - Maximum sample size for testing
  - Number of parallel workers
  - Visualization generation control

## Architecture

### Repository Structure

Based on the [repository structure](https://github.com/habeneyasu/ai-price-prediction-capstone), the project is organized as:

```
ai-price-prediction-capstone/
├── part-a-frontier/          # Part A: Frontier Models
│   ├── README.md            # Part A documentation
│   ├── data/                # Dataset storage
│   ├── notebooks/           # Analysis notebooks
│   └── src/                 # Source code
│       └── main.py          # Entry point
├── shared/                   # Shared utilities
│   └── price_prediction_utils/
│       ├── item.py          # Product data model
│       ├── frontier_models.py  # Model implementations
│       ├── predictor.py     # Prediction service
│       ├── evaluator.py     # Evaluation framework
│       ├── settings.py      # Configuration
│       ├── data_loader.py   # Data loading utilities
│       └── logging_config.py # Logging setup
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── README.md               # Project overview
```

### Shared Utilities Package

The `shared/price_prediction_utils/` package provides reusable components:

- **`item.py`**: Pydantic-based `Item` class for type-safe product representation
- **`frontier_models.py`**: Provider implementations (OpenRouter, Ollama)
- **`predictor.py`**: Abstraction layer for price prediction service
- **`evaluator.py`**: Evaluation framework with metrics and visualizations
- **`data_loader.py`**: Unified data loading (CSV, JSON, HuggingFace datasets)
- **`settings.py`**: Centralized configuration management from environment variables
- **`logging_config.py`**: Structured logging configuration

## Usage

### Quick Start

```bash
# Navigate to Part A
cd part-a-frontier/src

# Quick prediction with OpenRouter
python main.py --provider openrouter --predict "Wireless headphones with noise cancellation"

# Evaluate on sample data
python main.py --provider openrouter --model openai/gpt-4o --data sample --count 20

# Use local Ollama model
python main.py --provider ollama --model llama3.1 --data sample --count 10
```

### Configuration

Create a `.env` file in the project root:

```env
# OpenRouter API Key (for Part A)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Ollama Configuration (optional, for local models)
OLLAMA_BASE_URL=http://localhost:11434

# Model Configuration
MODEL_PROVIDER=openrouter
MODEL_NAME=openai/gpt-4o
MODEL_TEMPERATURE=0.3
MODEL_MAX_TOKENS=50

# Evaluation Configuration
EVAL_MAX_SAMPLES=200
EVAL_NUM_WORKERS=5
EVAL_GENERATE_PLOTS=true

# Logging
LOG_LEVEL=INFO
```

## Technical Implementation

### Model Provider Integration

#### OpenRouter Implementation
- **API Client**: Uses OpenAI-compatible client library (`openai` package)
- **Model Access**: Supports all models listed on OpenRouter platform
- **Error Handling**: Implements retry logic and error recovery
- **Cost Management**: Tracks API usage and token consumption

#### Ollama Implementation
- **Communication**: Direct HTTP REST API calls to local Ollama service
- **Model Support**: Works with any model installed via `ollama pull` command
- **Cost**: Zero API costs (local execution)
- **Use Cases**: Development, testing, and privacy-sensitive scenarios

### Prediction Pipeline

The prediction workflow follows these steps:

1. **Input Processing**: Accept product description as text input
2. **Provider Selection**: Determine model provider (OpenRouter or Ollama)
3. **Prompt Engineering**: Construct price prediction prompt from description
4. **API Request**: Send formatted request to selected provider
5. **Response Extraction**: Parse price value from model response
6. **Validation**: Ensure price is non-negative and within reasonable bounds
7. **Output Formatting**: Return price as float value

### Evaluation Workflow

The evaluation process implements:

1. **Data Loading**: Load test dataset using `data_loader.py` (supports CSV, JSON, HuggingFace)
2. **Parallel Prediction**: Generate predictions using ThreadPoolExecutor for efficiency
3. **Metric Computation**: Calculate MAE, MSE, and R² using scikit-learn
4. **Visualization Generation**: Create interactive Plotly charts
5. **Report Output**: Display metrics and visualizations in evaluation report

## Design Benefits

### 1. **Provider Abstraction**
- Unified interface allows switching between OpenRouter and Ollama
- Enables direct model performance comparison
- No code modifications required when testing different models

### 2. **Cost Efficiency**
- OpenRouter provides access to multiple models with competitive pricing
- Ollama enables zero-cost local inference for development
- Built-in usage tracking for cost monitoring

### 3. **Code Quality**
- Structured error handling and recovery mechanisms
- Comprehensive logging via `logging_config.py`
- Environment-based configuration for deployment flexibility
- Modular design with clear separation of concerns

### 4. **Evaluation Capabilities**
- Multiple statistical metrics for thorough assessment
- Interactive visualizations for error analysis
- Parallel processing for scalable evaluation

## Dependencies

Core dependencies include:

- `pydantic`: Data validation and modeling
- `openai`: OpenAI-compatible API client (for OpenRouter)
- `requests`: HTTP client (for Ollama)
- `pandas`, `numpy`: Data processing
- `scikit-learn`: Evaluation metrics
- `plotly`: Interactive visualizations
- `tqdm`: Progress bars
- `python-dotenv`: Environment variable management

## API Keys Setup

### OpenRouter
1. Sign up at [OpenRouter.ai](https://openrouter.ai)
2. Get API key from dashboard
3. Add to `.env`: `OPENROUTER_API_KEY=your_key`

### Ollama (Local)
1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Pull a model: `ollama pull llama3.1`
3. Start Ollama service (usually runs automatically)
4. Configure in `.env`: `OLLAMA_BASE_URL=http://localhost:11434`

## Results & Performance

Part A establishes baseline performance metrics for frontier models. The evaluation framework enables:

- **Comparative Analysis**: Side-by-side comparison of different frontier models
- **Performance Monitoring**: Track prediction accuracy metrics over evaluation runs
- **Error Pattern Analysis**: Identify systematic errors through visualization
- **Cost Tracking**: Monitor API usage and associated costs for OpenRouter calls

## Integration with Capstone Project

Part A establishes the foundation for the complete capstone project:

- **Part B (Fine-tuned Models)**: Open-source models fine-tuned with QLoRA will be benchmarked against Part A frontier model baselines
- **Part C (Autonomous Agents)**: The agent system will leverage Part A's prediction capabilities for deal detection and price monitoring

## Usage Recommendations

1. **Incremental Testing**: Begin with small sample datasets before full-scale evaluation
2. **Cost Monitoring**: Track API usage and costs, particularly with OpenRouter provider
3. **Development Workflow**: Utilize Ollama for local testing to minimize API costs during development
4. **Performance Optimization**: Configure appropriate worker count for parallel evaluation
5. **Analysis**: Review visualization outputs for insights beyond numerical metrics

## Potential Enhancements

Future improvements that could be implemented:

- [ ] Prediction caching to reduce redundant API calls
- [ ] Batch API support for OpenRouter to improve efficiency
- [ ] Advanced prompt engineering techniques
- [ ] Ensemble methods combining predictions from multiple models
- [ ] Real-time monitoring capabilities for price tracking

## Conclusion

Part A: Frontier Models implements a production-ready framework for price prediction using commercial frontier language models. The implementation establishes performance baselines and provides comprehensive evaluation capabilities that serve as the foundation for the subsequent parts of the capstone project. The dual-provider architecture (OpenRouter and Ollama) ensures flexibility for both development and production deployment scenarios.

---

## References

- **Repository**: [habeneyasu/ai-price-prediction-capstone](https://github.com/habeneyasu/ai-price-prediction-capstone)
- **Branch**: `feat/w6-part-a-price-prediction`
- **Dataset**: McAuley-Lab/Amazon-Reviews-2023 (HuggingFace)
- **OpenRouter**: [OpenRouter.ai](https://openrouter.ai)
- **Ollama**: [Ollama.ai](https://ollama.ai)
