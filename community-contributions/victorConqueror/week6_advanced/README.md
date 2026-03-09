# Advanced Price Predictor v2.0

An enhanced machine learning system for predicting product prices with improved accuracy using ensemble methods, RAG, and fine-tuned LLMs.

## 🎯 Goal
Beat the original Week 6 error rates ($56-96) by 40-50% using advanced techniques.

## 🔧 Improvements Implemented

1. **Enhanced Feature Engineering** - Brand extraction, text statistics, advanced features
2. **Text Embeddings** - Semantic understanding with sentence-transformers
3. **RAG System** - Retrieval-Augmented Generation with similar products
4. **Advanced Models** - XGBoost, Neural Networks, Fine-tuned LLMs
5. **Ensemble Learning** - Meta-learner combines multiple models
6. **Chain-of-Thought** - Reasoning-based LLM predictions
7. **Multi-Task Learning** - Joint prediction of price, category, and range
8. **Uncertainty Quantification** - Confidence intervals for predictions

## 📊 Expected Results

| Model | Expected Error | Improvement |
|-------|---------------|-------------|
| Enhanced XGBoost | $42-48 | 15-25% |
| Neural Net + Embeddings | $38-45 | 20-30% |
| Fine-tuned LLM + RAG | $35-42 | 25-40% |
| Ensemble (Combined) | $28-35 | 40-50% |

## 🗂️ Project Structure

```
week6_advanced/
├── data/                    # Cached data and models
├── src/                     # Source code modules
│   ├── items.py            # Enhanced Item class
│   ├── features.py         # Feature engineering
│   ├── embeddings.py       # Text embeddings
│   ├── rag.py             # RAG system
│   ├── models/            # Model implementations
│   ├── ensemble.py        # Meta-learner
│   └── evaluator.py       # Evaluation utilities
├── notebooks/              # Jupyter notebooks
└── requirements.txt        # Dependencies
```

## 🚀 Getting Started

### Two Ways to Use This Project:

#### Option 1: Jupyter Notebooks (Training & Learning)
```bash
pip install -r requirements.txt
jupyter notebook notebooks/01_data_prep.ipynb
```

Run notebooks in order:
- `01_data_prep.ipynb` - Load and prepare data
- `02_rag_setup.ipynb` - Build RAG system
- `03_train_models.ipynb` - Train individual models
- `04_ensemble.ipynb` - Create ensemble
- `05_evaluation.ipynb` - Evaluate results

#### Option 2: Gradio Web UI (Production Use)
```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:7860 in your browser!

**See [UI_GUIDE.md](UI_GUIDE.md) for detailed UI instructions.**

## 📝 Author
Victor Conqueror - Week 6 Advanced Project
