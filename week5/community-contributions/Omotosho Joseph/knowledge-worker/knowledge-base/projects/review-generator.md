# Synthetic Product Review Generator - Project Documentation

## Overview
A Google Colab notebook that loads quantized open-source LLMs and generates synthetic product reviews across multiple dimensions.

## Architecture
- **Platform**: Google Colab with T4 GPU (free tier)
- **Models**: LLaMA 3.2 3B, Qwen 2.5 3B (loaded one at a time)
- **Quantization**: BitsAndBytesConfig for 4-bit quantization
- **UI**: Gradio with yield generators for real-time progress streaming
- **Output**: Downloadable JSON file

## Key Concepts

### Quantization
Quantization reduces model precision from 32-bit floats to 4-bit integers. This dramatically reduces memory usage (roughly 8x) so large models can fit on consumer GPUs. BitsAndBytesConfig handles the conversion automatically. The tradeoff is a small quality reduction that's usually acceptable for most tasks.

### Chat Templates
Each model family has its own chat template format. The tokenizer handles applying the correct template. For example, LLaMA uses a different special token format than Qwen. Using the wrong template causes garbage outputs.

### HuggingFace Pipeline
The pipeline abstraction wraps model + tokenizer into a single callable. You specify the task (e.g., "text-generation") and get a simple interface. Under the hood, it handles tokenization, inference, and decoding.

## Generation Strategy
Reviews are generated across three dimensions: model (LLaMA vs Qwen), product (5 categories), and sentiment (positive, negative, neutral). Each combination produces multiple reviews. This creates a balanced synthetic dataset.

## Lessons Learned
- 4-bit quantization makes 3B parameter models practical on free Colab GPUs
- Loading models one at a time avoids OOM errors
- Gradio yield generators provide excellent real-time feedback during long generation runs
- Chat templates are critical - wrong templates produce incoherent outputs
