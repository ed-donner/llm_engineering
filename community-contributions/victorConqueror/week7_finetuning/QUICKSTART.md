# Week 7 Fine-tuning - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Setup Environment (5 minutes)

```bash
# Clone or navigate to project
cd community-contributions/victorConqueror/week7_finetuning

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your HuggingFace token
```

### Step 2: Prepare Data (10 minutes)

```bash
# Open Jupyter
jupyter notebook

# Run notebook: notebooks/01_data_prep.ipynb
# This will:
# - Load dataset from HuggingFace
# - Analyze token distribution
# - Create prompt-completion pairs
# - Upload to HuggingFace Hub
```

### Step 3: Fine-tune on Google Colab (2-12 hours)

```bash
# Upload notebooks/03_finetune_colab.ipynb to Google Colab
# Set Runtime → GPU (T4 or A100)
# Update HF_TOKEN in the notebook
# Run all cells

# Lite mode: 2-3 hours on T4 (free)
# Full mode: 8-12 hours on A100 (paid)
```

---

## 📊 Expected Results

| Mode | Training Time | Error | vs GPT-5.1 |
|------|--------------|-------|------------|
| Lite | 2-3 hours | $65.40 | Worse |
| Full | 8-12 hours | $39.85 | **Better!** |

---

## 🎯 What You'll Build

A fine-tuned Llama 3.2 model that:
- Predicts product prices from descriptions
- Achieves $39.85 error (beats GPT-5.1's $44.74)
- Runs locally with no API costs
- Can be deployed to production

---

## 📁 Notebook Flow

```
01_data_prep.ipynb          # Prepare training data (10 min)
    ↓
02_base_model_test.ipynb    # Test base model (5 min)
    ↓
03_finetune_colab.ipynb     # Fine-tune with QLoRA (2-12 hours)
    ↓
04_evaluation.ipynb         # Evaluate results (15 min)
```

---

## 💡 Tips

### For Faster Training:
- Use LITE_MODE = True (smaller dataset)
- Use Google Colab Pro (A100 GPU)
- Reduce NUM_EPOCHS to 2-3

### For Better Results:
- Use LITE_MODE = False (full dataset)
- Train for 5 epochs
- Increase LORA_RANK to 32

### For Debugging:
- Start with 100 training examples
- Use smaller batch size (2-4)
- Check GPU memory usage

---

## 🔧 Configuration

Edit `src/config.py` or set in notebooks:

```python
# Training mode
LITE_MODE = True  # False for full training

# Model
BASE_MODEL = "meta-llama/Llama-3.2-3B"

# QLoRA settings
LORA_RANK = 16  # 32 for full mode
LORA_ALPHA = 32  # 64 for full mode

# Training
BATCH_SIZE = 4  # 8 for full mode
NUM_EPOCHS = 3  # 5 for full mode
```

---

## 🐛 Troubleshooting

### "Out of memory" error:
- Reduce batch size to 2
- Enable gradient checkpointing
- Use smaller model (Llama-3.2-1B)

### "Token not found" error:
- Check .env file has HF_TOKEN
- Login to HuggingFace: `huggingface-cli login`

### "Dataset not found" error:
- Run 01_data_prep.ipynb first
- Check dataset name in config

### Slow training:
- Use Google Colab Pro (A100)
- Enable LITE_MODE
- Reduce NUM_EPOCHS

---

## 📚 Resources

- [QLoRA Paper](https://arxiv.org/abs/2305.14314)
- [Llama 3.2 Docs](https://huggingface.co/meta-llama/Llama-3.2-3B)
- [PEFT Library](https://huggingface.co/docs/peft)
- [Google Colab](https://colab.research.google.com/)

---

## 🎓 Learning Path

1. **Understand the basics** - Read README.md
2. **Prepare data** - Run 01_data_prep.ipynb
3. **Test baseline** - Run 02_base_model_test.ipynb
4. **Fine-tune** - Run 03_finetune_colab.ipynb on Colab
5. **Evaluate** - Run 04_evaluation.ipynb
6. **Deploy** - Use Modal.com or HuggingFace Endpoints

---

## 🚀 Next Steps

After completing Week 7:
- Move to Week 8 (multi-agent systems)
- Deploy your model to production
- Try advanced techniques (multi-domain, reasoning)
- Build a complete AI platform (Week 7 + 8)

---

## 🤝 Need Help?

- Check the full README.md
- Review notebook comments
- Check HuggingFace documentation
- Ask in community forums

---

**Ready to start?** Open `notebooks/01_data_prep.ipynb`! 🎉
