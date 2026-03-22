# Resume Role Predictor with Fine-Tuned LLaMA 3B

This project demonstrates how to fine-tune a **meta-llama/Llama-3.2-3B** model to predict job roles from synthetic resume summaries.

## Project Overview
A curated dataset of synthetic resume summaries and their corresponding job roles is used to fine-tune a LLaMA 3B model using **LoRA adapters** and **4-bit quantization**. The goal is to predict the job role given a resume summary, which can then be tested interactively through a **Gradio interface**.

## Key Features
- **LoRA Fine-Tuning**: Efficient parameter-efficient fine-tuning on a 3B model with minimal GPU memory.  
- **4-bit Quantization**: Reduces memory usage while maintaining inference speed.  
- **Small Dataset Support**: Fine-tuned on a lightweight dataset of synthetic resumes for rapid experimentation.  
- **Interactive Gradio UI**: Allows users to input a resume summary and get predicted job roles in real time.  
- **Hugging Face Hub Integration**: Push fine-tuned adapters for easy sharing and reuse.

## Workflow
1. **Data Loading**: Load the synthetic resume summaries dataset from Hugging Face.  
2. **Tokenization**: Prepare sequences with padding/truncation.  
3. **LoRA + QLoRA Setup**: Configure LoRA adapters and 4-bit quantization for memory-efficient fine-tuning.  
4. **Fine-Tuning**: Train the LoRA adapters with the SFTTrainer from `trl`.  
5. **Inference**: Load the fine-tuned adapter and generate predictions using the LLaMA base model.  
6. **Gradio Deployment**: Provide a simple web UI for interactive testing.

# Setup Guide for Resume Role Predictor (Fine-Tuned LLaMA 3B)

## 1. Environment
- Recommended: **Google Colab** or a GPU machine with **≥12GB GPU memory**.  
- Python 3.10+  
- Ensure you have **CUDA-enabled PyTorch** installed for GPU acceleration.

## 2. Install Required Packages
Run the following commands in your notebook or terminal:

```bash
# Core libraries
!pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Transformers, PEFT, TRL for LoRA fine-tuning
!pip install -q --upgrade transformers==4.35.0 datasets bitsandbytes==0.48.2 trl==0.25.1 peft

# Optional: for logging and experiment tracking
!pip install wandb gradio