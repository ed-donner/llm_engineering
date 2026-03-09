# UI Options Guide

You have **TWO ways** to use this project:

---

## Option 1: Jupyter Notebooks (Learning & Training) 📓

**Best for:**
- Learning how everything works
- Training models
- Experimenting with features
- Data analysis and visualization

**How to use:**
```bash
jupyter notebook notebooks/01_data_prep.ipynb
```

**Notebooks:**
1. `01_data_prep.ipynb` - Data preparation
2. `02_rag_setup.ipynb` - RAG system
3. `03_train_models.ipynb` - Train models
4. `04_ensemble.ipynb` - Ensemble & LLM
5. `05_evaluation.ipynb` - Final evaluation

**Pros:**
- ✅ Interactive cells
- ✅ Inline visualizations
- ✅ Step-by-step execution
- ✅ Great for learning
- ✅ Can modify code easily

**Cons:**
- ❌ Not user-friendly for non-technical users
- ❌ Requires running cells manually

---

## Option 2: Gradio Web UI (Production Use) 🌐

**Best for:**
- Making predictions quickly
- Sharing with non-technical users
- Production deployment
- Demo purposes

**How to launch:**

### Windows:
```bash
launch_ui.bat
```

### Mac/Linux:
```bash
chmod +x launch_ui.sh
./launch_ui.sh
```

### Or directly:
```bash
python app.py
```

**Access at:** http://localhost:7860

**Features:**
- ✅ Beautiful web interface
- ✅ Easy to use (no coding required)
- ✅ Real-time predictions
- ✅ Shows all model predictions
- ✅ Displays similar products
- ✅ Pre-filled examples
- ✅ Can share with others

**Pros:**
- ✅ User-friendly
- ✅ Professional looking
- ✅ No coding needed
- ✅ Can share link
- ✅ Mobile-friendly

**Cons:**
- ❌ Requires trained models first
- ❌ Less flexibility than notebooks

---

## Recommended Workflow

### Phase 1: Training (Use Notebooks)
1. Run `01_data_prep.ipynb` - Prepare data
2. Run `02_rag_setup.ipynb` - Build RAG
3. Run `03_train_models.ipynb` - Train models
4. Run `04_ensemble.ipynb` - Create ensemble

### Phase 2: Usage (Use Gradio UI)
1. Launch: `python app.py`
2. Load models (click button)
3. Enter product details
4. Get instant predictions!

---

## Gradio UI Features

### 1. Model Loading
- Click "Load Models" button
- Loads XGBoost, Neural Network, and RAG system
- Shows status message

### 2. Product Input
- **Title**: Product name
- **Category**: Select from dropdown
- **Description**: Detailed product info
- **Weight**: Optional (in ounces)
- **Brand**: Optional

### 3. Predictions
- **Ensemble**: Final prediction (most accurate)
- **XGBoost**: Traditional ML prediction
- **Neural Network**: Deep learning prediction
- **RAG Baseline**: Similar products average
- **Similar Products**: Shows 5 most similar items

### 4. Examples
- Pre-filled examples to try
- Click any example to auto-fill form
- Covers different categories

---

## UI Screenshots (What to Expect)

### Gradio Interface Layout:
```
┌─────────────────────────────────────────────────────┐
│  🎯 Advanced Price Predictor v2.0                   │
├─────────────────────────────────────────────────────┤
│  [🔄 Load Models]  Status: ✅ Models loaded         │
├─────────────────────────────────────────────────────┤
│  Product Information          │  Predictions         │
│  ┌─────────────────────────┐  │  ┌────────────────┐ │
│  │ Title: [input]          │  │  │ Ensemble: $299 │ │
│  │ Category: [dropdown]    │  │  │ XGBoost: $295  │ │
│  │ Description: [textarea] │  │  │ Neural Net:$302│ │
│  │ Weight: [number]        │  │  │ RAG: $290      │ │
│  │ Brand: [input]          │  │  └────────────────┘ │
│  └─────────────────────────┘  │                      │
│  [💰 Predict Price]           │  Similar Products:   │
│                                │  1. Product A - $285│
│                                │  2. Product B - $310│
├─────────────────────────────────────────────────────┤
│  Examples: [Samsung TV] [KitchenAid] [Dewalt]      │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start Guide

### For First-Time Users:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Train models (one-time):**
   ```bash
   jupyter notebook notebooks/01_data_prep.ipynb
   # Run all cells in notebooks 01-04
   ```

3. **Launch UI:**
   ```bash
   python app.py
   ```

4. **Use the interface:**
   - Click "Load Models"
   - Try an example or enter your own product
   - Click "Predict Price"
   - See results!

---

## Advanced: Customizing the UI

### Change Port:
Edit `app.py`, line at bottom:
```python
demo.launch(server_port=8080)  # Change from 7860
```

### Enable Sharing:
```python
demo.launch(share=True)  # Creates public link
```

### Add Authentication:
```python
demo.launch(auth=("username", "password"))
```

### Custom Theme:
```python
gr.Blocks(theme=gr.themes.Glass())  # Try: Soft, Glass, Monochrome
```

---

## Troubleshooting

### "Models not found" error:
- Run training notebooks first (01-04)
- Check that `data/models/` folder exists

### Port already in use:
- Change port in `app.py`
- Or kill process: `lsof -ti:7860 | xargs kill`

### Slow predictions:
- Normal for first prediction (model loading)
- Subsequent predictions are fast
- Use GPU for faster neural network

### UI not loading:
- Check firewall settings
- Try `server_name="127.0.0.1"` instead of "0.0.0.0"

---

## Comparison: Notebooks vs Gradio

| Feature | Notebooks | Gradio UI |
|---------|-----------|-----------|
| **Ease of Use** | Medium | Easy |
| **Learning** | Excellent | Limited |
| **Speed** | Slow (manual) | Fast |
| **Sharing** | Hard | Easy |
| **Customization** | Full | Limited |
| **Production** | No | Yes |
| **Visualization** | Excellent | Basic |
| **Best For** | Training | Inference |

---

## Recommendation

**Use BOTH:**
1. **Notebooks** for training and understanding
2. **Gradio UI** for making predictions and demos

This gives you the best of both worlds! 🎉

---

## Next Steps

1. ✅ Train models using notebooks
2. ✅ Launch Gradio UI
3. ✅ Make predictions
4. 🚀 Share with others!

**Questions?** Check README.md or QUICKSTART.md

**Ready to start?** Run: `python app.py`
