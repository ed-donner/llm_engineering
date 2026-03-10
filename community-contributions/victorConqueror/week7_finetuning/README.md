# Week 7: Fine-tuning Llama 3.2 for Price Prediction

## 🎯 Project Goal
Fine-tune Llama 3.2 (3B parameters) using QLoRA to predict product prices from descriptions - achieving performance better than GPT-5.1!

## 📊 Expected Results
- **Base Llama 3.2**: $110.72 error (terrible)
- **Fine-tuned Lite**: $65.40 error (good)
- **Fine-tuned Full**: $39.85 error (excellent - beats GPT-5.1!)

## 🚀 Quick Start

### Option 1: Run Locally (if you have GPU)
```bash
cd community-contributions/victorConqueror/week7_finetuning
pip install -r requirements.txt
jupyter notebook notebooks/01_data_prep.ipynb
```

### Option 2: Run on Google Colab (Recommended)
1. Open `notebooks/01_data_prep.ipynb` in Colab
2. Follow notebooks in order: 01 → 02 → 03 → 04
3. Use free T4 GPU or paid A100 for faster training

## 📁 Project Structure

```
week7_finetuning/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment variables template
├── notebooks/
│   ├── 01_data_prep.ipynb            # Prepare training data
│   ├── 02_base_model_test.ipynb      # Test base Llama (before fine-tuning)
│   ├── 03_finetune_colab.ipynb       # Fine-tune on Colab (MAIN TRAINING)
│   └── 04_evaluation.ipynb           # Evaluate fine-tuned model
├── src/
│   ├── __init__.py
│   ├── items.py                       # Item class & data handling
│   ├── evaluator.py                   # Evaluation & visualization
│   └── config.py                      # Configuration settings
└── models/                            # Saved models (created during training)
    └── .gitkeep
```

## 📝 Step-by-Step Guide

### Step 1: Data Preparation (01_data_prep.ipynb)
- Load dataset from HuggingFace Hub
- Analyze token distribution
- Create prompt-completion pairs
- Upload to HuggingFace Hub

**Time:** 10-15 minutes

### Step 2: Test Base Model (02_base_model_test.ipynb)
- Load base Llama 3.2 in 4-bit quantization
- Test on sample products
- Establish baseline performance (~$110 error)

**Time:** 5-10 minutes

### Step 3: Fine-tune with QLoRA (03_finetune_colab.ipynb)
- Configure QLoRA parameters
- Train with SFTTrainer
- Save LoRA adapters to HuggingFace Hub

**Time:** 
- Lite mode: 2-3 hours (T4 GPU)
- Full mode: 8-12 hours (A100 GPU)

### Step 4: Evaluation (04_evaluation.ipynb)
- Load fine-tuned model
- Run on test set
- Generate visualizations
- Compare with all models

**Time:** 15-20 minutes

## 🔧 Configuration

### Environment Variables (.env)
```bash
HF_TOKEN=your_huggingface_token_here
OPENAI_API_KEY=your_openai_key_here  # Optional, for comparison
```

### Training Modes
- **LITE_MODE = True**: Smaller dataset, faster training (~50k examples)
- **LITE_MODE = False**: Full dataset, best results (~640k examples)

### Model Settings
- **Base Model**: meta-llama/Llama-3.2-3B
- **Quantization**: 4-bit (bitsandbytes)
- **LoRA Rank**: 16 (lite) or 32 (full)
- **Max Tokens**: 110 (product description cutoff)

## 📊 What You'll Get

### Visualizations
1. **Token Distribution Chart** - analyze input lengths
2. **Scatter Plot** - predicted vs actual prices
3. **Error Trend Chart** - running average with confidence intervals
4. **Comparison Bar Chart** - all models side-by-side

### Metrics
- Mean Absolute Error (MAE)
- Mean Squared Error (MSE)
- R² Score
- Color-coded predictions (green/orange/red)

### Saved Models
- LoRA adapters on HuggingFace Hub
- Can be loaded and merged with base model
- Ready for production deployment

## 💡 Key Concepts

### QLoRA (Quantized Low-Rank Adaptation)
- Quantize base model to 4-bit → reduces memory
- Add small trainable adapters → only train 2% of parameters
- Merge adapters at inference → full model performance

### Prompt Format
```
What does this cost to the nearest dollar?

[Product description - max 110 tokens]

Price is $
```

### Training Strategy
- Supervised Fine-Tuning (SFT) on prompt-completion pairs
- Learning rate: 2e-4
- Batch size: 4-8 (depending on GPU)
- Epochs: 3-5
- Gradient accumulation: 4

## 🎓 Learning Outcomes

After completing this project, you'll understand:
- ✅ How to fine-tune large language models efficiently
- ✅ QLoRA and parameter-efficient training
- ✅ Prompt engineering for training data
- ✅ Model evaluation and comparison
- ✅ How open-source can beat frontier models
- ✅ Production deployment strategies

## 🚀 Next Steps

### Improvements You Can Make:
1. **Multi-domain adapters** - separate adapter per category
2. **Reasoning chains** - teach model to explain predictions
3. **Confidence scores** - add uncertainty estimates
4. **Continuous learning** - update with new data
5. **Ensemble methods** - combine multiple adapters

### Deploy to Production:
- Modal.com (serverless)
- HuggingFace Inference Endpoints
- Local server with FastAPI
- AWS SageMaker

## 📚 Resources

- [QLoRA Paper](https://arxiv.org/abs/2305.14314)
- [Llama 3.2 Model Card](https://huggingface.co/meta-llama/Llama-3.2-3B)
- [PEFT Documentation](https://huggingface.co/docs/peft)
- [TRL Documentation](https://huggingface.co/docs/trl)

## 🤝 Credits

Based on Week 7 curriculum from LLM Engineering course.
Dataset: Ed's Items (800k products from various categories)

## 📄 License

MIT License - feel free to use and modify for your projects!

---

**Ready to fine-tune?** Start with `notebooks/01_data_prep.ipynb`! 🚀
