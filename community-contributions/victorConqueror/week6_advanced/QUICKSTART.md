# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
cd community-contributions/victorConqueror/week6_advanced
pip install -r requirements.txt
```

### Step 2: Set Up Environment

Create a `.env` file in the project root:

```bash
# .env file
HF_TOKEN=your_huggingface_token_here
OPENAI_API_KEY=your_openai_key_here  # For fine-tuning later
```

Get your HuggingFace token: https://huggingface.co/settings/tokens

### Step 3: Run Data Preparation

Open and run the first notebook:

```bash
jupyter notebook notebooks/01_data_prep.ipynb
```

This will:
- Load the dataset (ed-donner/items_lite)
- Extract enhanced features
- Generate embeddings
- Save processed data

**Time:** ~5-10 minutes

### Step 4: What You'll Get

After running the notebook, you'll have:

```
data/
├── train_features.csv          # Engineered features
├── val_features.csv
├── test_features.csv
├── train_prices.npy           # Target prices
├── val_prices.npy
├── test_prices.npy
└── embeddings/
    ├── train_embeddings.npy   # Text embeddings
    ├── val_embeddings.npy
    └── test_embeddings.npy
```

## 📊 Quick Test

Test the enhanced features:

```python
from src.items import Item

# Load data
train, val, test = Item.from_hub("ed-donner/items_lite")

# Enhance a single item
item = train[0]
item.enhance()

# Check new features
print(f"Brand: {item.brand}")
print(f"Is Premium: {item.is_premium}")
print(f"Price Bucket: {item.price_bucket}")
print(f"Word Count: {item.word_count}")
```

## 🎯 Next Steps

1. ✅ **Completed:** Data preparation
2. 📝 **Next:** Build RAG system (notebook 02)
3. 📝 **Then:** Train models (notebook 03)
4. 📝 **Finally:** Create ensemble (notebook 04)

## 🔍 Verify Installation

Run this to check everything is installed:

```python
import torch
import xgboost
import sentence_transformers
import faiss
import pandas as pd
import numpy as np

print("✅ All dependencies installed!")
print(f"PyTorch: {torch.__version__}")
print(f"XGBoost: {xgboost.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
```

## 💡 Tips

- **Use GPU:** If you have CUDA, the neural network will train much faster
- **Start Small:** Use the lite dataset (20k items) for quick experiments
- **Cache Embeddings:** Embeddings are cached automatically to save time
- **Monitor Progress:** All notebooks show progress bars

## 🐛 Troubleshooting

### Issue: HuggingFace login fails
```bash
# Login manually
huggingface-cli login
```

### Issue: FAISS installation fails
```bash
# Use CPU version
pip install faiss-cpu
```

### Issue: Out of memory
```bash
# Reduce batch size in notebooks
batch_size = 16  # Instead of 64
```

## 📚 Documentation

- **README.md** - Project overview
- **PROJECT_SUMMARY.md** - Detailed implementation summary
- **requirements.txt** - All dependencies
- **notebooks/** - Step-by-step tutorials

## 🎓 Learning Path

1. **Beginner:** Run notebooks 01-03, understand basic models
2. **Intermediate:** Experiment with hyperparameters, try different features
3. **Advanced:** Implement ensemble, fine-tune LLM, optimize performance

## 🤝 Need Help?

- Check PROJECT_SUMMARY.md for detailed explanations
- Review the original week6 notebooks for context
- Each module has docstrings explaining functionality

---

**Ready to build the best price predictor?** 🚀

Start with: `jupyter notebook notebooks/01_data_prep.ipynb`
