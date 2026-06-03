# Part B: Fine-tuned Models - Implementation Summary

**Repository**: [ai-price-prediction-capstone](https://github.com/habeneyasu/ai-price-prediction-capstone)  
**Part**: Part B - Fine-tuned Models (Week 7)  
**Status**: ✅ Completed  
**Branch**: `main`

---

## Overview

Part B implements a fine-tuning pipeline for open-source language models to compete with frontier commercial models in price prediction. This component uses QLoRA (Quantized Low-Rank Adaptation) for parameter-efficient fine-tuning, enabling adaptation of large models like LLaMA 3.1-8B for price prediction tasks without full model fine-tuning.

The implementation provides a cost-effective alternative to commercial frontier models, allowing open-source models to achieve competitive performance through task-specific optimization.

## Key Features

### 1. **QLoRA Fine-Tuning Pipeline**
- **Parameter-Efficient Fine-Tuning**: QLoRA technique for memory-efficient adaptation
  - 4-bit quantization reduces memory requirements
  - Low-rank adaptation matrices for task-specific learning
  - Enables fine-tuning on consumer hardware
- **PEFT Integration**: HuggingFace PEFT library for efficient fine-tuning
  - Minimal parameter updates (only adapter weights)
  - Preserves base model weights
  - Supports multiple adapter configurations
- **Model Support**: Fine-tunes LLaMA 3.1-8B with quantization
  - 8 billion parameter model quantized to 4-bit
  - Competitive performance with frontier models

### 2. **Training Infrastructure**
- **HuggingFace Integration**: Full ecosystem integration
  - Model and dataset loading from HuggingFace Hub
  - Model checkpointing and versioning
- **Training Configuration**: Configurable hyperparameters
  - Learning rate, batch size, epochs
  - Training and validation loss tracking
  - Gradient accumulation for larger effective batches
- **Memory Optimization**: 4-bit quantization via BitsAndBytes, gradient checkpointing

### 3. **Evaluation and Benchmarking**
- **Performance Comparison**: Direct comparison with Part A frontier models
  - Same evaluation metrics (MAE, MSE, R²) and test dataset
  - Performance tracking across training epochs
- **Baseline Comparison**: Pre and post-fine-tuning performance metrics

## Architecture

### Repository Structure

Based on the [repository structure](https://github.com/habeneyasu/ai-price-prediction-capstone), Part B is organized as:

```
ai-price-prediction-capstone/
├── part-b-finetune/          # Part B: Fine-tuned Models
│   ├── README.md            # Part B documentation
│   ├── data/                # Training and validation datasets
│   ├── models/              # Fine-tuned model checkpoints
│   └── src/                 # Source code
│       ├── training.py      # Training pipeline
│       ├── evaluation.py    # Evaluation scripts
│       └── inference.py     # Inference utilities
├── shared/                   # Shared utilities (from Part A)
│   └── price_prediction_utils/
│       ├── item.py          # Product data model
│       ├── evaluator.py     # Evaluation framework
│       ├── data_loader.py   # Data loading utilities
│       └── settings.py      # Configuration management
├── requirements.txt         # Python dependencies
└── .env.example            # Environment variables template
```

### Shared Utilities Package

Part B leverages the shared utilities from Part A:

- **`item.py`**: Product data model for consistent data representation
- **`evaluator.py`**: Evaluation framework with metrics and visualizations
- **`data_loader.py`**: Dataset loading utilities (CSV, JSON, HuggingFace)
- **`settings.py`**: Configuration management

## Technical Implementation

### QLoRA Fine-Tuning Process

The fine-tuning pipeline follows these steps:

1. **Model Preparation**: Load base model (LLaMA 3.1-8B) with 4-bit quantization using BitsAndBytes
2. **LoRA Configuration**: Configure low-rank adaptation matrices targeting attention layers
3. **Data Preprocessing**: Format product descriptions for instruction-following format
4. **Training**: Fine-tune only LoRA adapter parameters while base model remains frozen
5. **Validation**: Monitor validation loss to prevent overfitting
6. **Checkpointing**: Save adapter weights periodically

### Training Configuration

**Key Hyperparameters**:
- Learning Rate: 2e-4 to 5e-4 (typical for LoRA)
- Batch Size: Configurable with gradient accumulation
- Epochs: 1-3 epochs (often sufficient with QLoRA)
- LoRA Rank (r): 8-32 (capacity vs efficiency trade-off)
- LoRA Alpha: Typically 2x the rank value

**Training Features**:
- Gradient accumulation for larger effective batches
- Mixed precision training (FP16/BF16)
- Learning rate scheduling
- Early stopping based on validation metrics

### Inference

Fine-tuned models load base model with saved adapter weights and generate price predictions using the same evaluation framework as Part A.

## Usage

### Training

```bash
cd part-b-finetune/src
python training.py --model_name meta-llama/Llama-3.1-8B \
    --dataset_path ./data/train.jsonl \
    --output_dir ./models/llama-3.1-8b-pricer \
    --lora_r 16 --lora_alpha 32 \
    --learning_rate 2e-4 --num_epochs 3
```

### Evaluation

```bash
python evaluation.py --model_path ./models/llama-3.1-8b-pricer \
    --test_data ./data/test.jsonl --output_dir ./results
```

### Configuration

Environment variables (`.env` file):

```env
# HuggingFace Token (required)
HF_TOKEN=your_huggingface_token_here

# Model Configuration
BASE_MODEL=meta-llama/Llama-3.1-8B
MODEL_QUANTIZATION=4bit

# Training Configuration
LORA_R=16
LORA_ALPHA=32
LEARNING_RATE=2e-4
BATCH_SIZE=4
NUM_EPOCHS=3

# Evaluation Configuration
EVAL_MAX_SAMPLES=200
EVAL_NUM_WORKERS=5
EVAL_GENERATE_PLOTS=true
```

## Dependencies

Core dependencies for Part B:

- **`transformers`**: HuggingFace transformers library
- **`peft`**: Parameter-Efficient Fine-Tuning library
- **`bitsandbytes`**: 4-bit quantization support
- **`accelerate`**: Training acceleration utilities
- **`datasets`**: HuggingFace datasets library
- **`torch`**: PyTorch deep learning framework
- **`pydantic`**: Data validation (from shared utilities)
- **`scikit-learn`**: Evaluation metrics
- **`plotly`**: Visualizations (from shared utilities)

## Key Advantages

### 1. **Cost Efficiency**
- No API costs - models run locally
- QLoRA enables fine-tuning on consumer GPUs
- Reusable models after one-time training

### 2. **Performance Competitiveness**
- Fine-tuned models can match or exceed frontier model performance
- Task-specific optimization for price prediction
- Deterministic outputs without API variability

### 3. **Flexibility and Control**
- Full control over training process
- Model versioning for different experiments
- Privacy - no data sent to external APIs
- Offline capability

### 4. **Parameter Efficiency**
- Minimal storage - only adapter weights (~100MB vs 16GB)
- Multiple adapters for different tasks
- Base model weights remain unchanged

## Results & Performance

Part B demonstrates that fine-tuned open-source models achieve competitive performance:

- Fine-tuned models benchmarked against Part A frontier model baselines
- Performance metrics (MAE, MSE, R²) tracked and compared
- QLoRA enables efficient training with minimal resources
- Significant cost savings compared to API-based solutions

**Performance Improvements**:
- Pre-fine-tuning: Baseline LLaMA 3.1-8B zero-shot performance
- Post-fine-tuning: Improved accuracy with task-specific adaptation
- Comparison: Performance relative to frontier models from Part A

## Integration with Capstone Project

Part B builds upon Part A and prepares for Part C:

- Fine-tuned models benchmarked against Part A frontier model results
- Uses same evaluation framework as Part A for fair comparison
- Fine-tuned models available for Part C autonomous agent system
- Provides cost-effective alternative to frontier models

## Best Practices

### Training
- Start with smaller LoRA rank (r=8) and increase if needed
- Monitor validation loss to prevent overfitting
- Experiment with learning rates and LoRA configurations
- Ensure high-quality, consistently formatted training data
- Save checkpoints regularly during training

### Evaluation
- Use identical test datasets as Part A for fair comparison
- Average results across multiple evaluation runs
- Review failure cases for improvement opportunities
- Always compare against pre-fine-tuning baseline

### Resource Management
- Monitor GPU memory and adjust batch size accordingly
- QLoRA reduces training time significantly vs full fine-tuning
- Only adapter weights need storage (~100MB vs 16GB)
- Ensure HuggingFace token access for model downloads

## Potential Enhancements

Future improvements:

- Multi-task fine-tuning for related pricing tasks
- Ensemble methods combining multiple fine-tuned models
- Advanced prompt engineering for better inference
- Model distillation for smaller, faster inference
- Continuous learning from new data
- Integration with vector databases for RAG
- Automated hyperparameter optimization

## Comparison with Part A

| Aspect | Part A (Frontier Models) | Part B (Fine-tuned Models) |
|--------|-------------------------|---------------------------|
| **Model Type** | Commercial API models | Open-source fine-tuned |
| **Cost** | Per-request API costs | One-time training cost |
| **Setup** | API keys required | Local training required |
| **Performance** | Strong baseline | Competitive after fine-tuning |
| **Flexibility** | Limited to API capabilities | Full model control |
| **Privacy** | Data sent to external APIs | Local processing |
| **Scalability** | API rate limits | Unlimited local inference |

## Conclusion

Part B: Fine-tuned Models demonstrates that parameter-efficient fine-tuning with QLoRA enables open-source models to achieve competitive performance in price prediction tasks. The implementation provides a cost-effective alternative to commercial frontier models while maintaining full control over model behavior.

The fine-tuning pipeline integrates with shared utilities from Part A, ensuring consistent evaluation and comparison. The resulting models serve as a foundation for Part C, where they will be integrated into an autonomous agent system for deal detection and price monitoring.

---

## References

- **Repository**: [habeneyasu/ai-price-prediction-capstone](https://github.com/habeneyasu/ai-price-prediction-capstone)
- **Branch**: `main`
- **Dataset**: McAuley-Lab/Amazon-Reviews-2023 (HuggingFace)
- **Base Model**: [meta-llama/Llama-3.1-8B](https://huggingface.co/meta-llama/Llama-3.1-8B)
- **PEFT Library**: [HuggingFace PEFT](https://github.com/huggingface/peft)
- **QLoRA Paper**: "QLoRA: Efficient Finetuning of Quantized LLMs" (Dettmers et al., 2023)
