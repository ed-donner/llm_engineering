# 📦 VoiceScribe AI - Installation Guide

Complete step-by-step installation instructions for VoiceScribe AI.

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.8+** installed ([Download Python](https://www.python.org/downloads/))
- **pip** package manager (comes with Python)
- **8GB+ RAM** (16GB recommended)
- **CUDA-compatible GPU** (optional, but recommended for faster processing)
- **5-10GB free disk space** (for models and dependencies)

---

## Installation Methods

### Method 1: Automated Setup (Recommended)

#### On macOS/Linux:

```bash
cd "VoiceScribe AI"
chmod +x setup.sh
./setup.sh
```

#### On Windows:

```bash
cd "VoiceScribe AI"
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Method 2: Manual Setup

#### Step 1: Navigate to Project Directory

```bash
cd "VoiceScribe AI"
```

#### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

#### Step 3: Upgrade pip

```bash
pip install --upgrade pip
```

#### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Gradio (UI framework)
- PyTorch (deep learning)
- Transformers (AI models)
- LangChain (RAG framework)
- FAISS (vector database)
- And other required packages

---

## GPU Setup (Optional)

### For NVIDIA GPUs with CUDA:

1. Install CUDA toolkit ([Download CUDA](https://developer.nvidia.com/cuda-downloads))

2. Install PyTorch with CUDA support:

```bash
# For CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

3. Install FAISS-GPU (optional, for faster vector search):

```bash
pip uninstall faiss-cpu
pip install faiss-gpu
```

4. Verify GPU setup:

```bash
python -c "import torch; print('GPU Available:', torch.cuda.is_available())"
```

---

## Running the Application

### Start the Application:

```bash
python voicescribe_ai.py
```

The application will:
1. Load all AI models (may take 2-5 minutes on first run)
2. Start a local web server
3. Open automatically in your browser
4. Display a public shareable URL

### Expected Output:

```
========================================
🚀 Starting VoiceScribe AI...
========================================
Loading Whisper model on cuda...
Loading summarization model...
Loading embeddings model for RAG...
Loading QA model...
✅ All models loaded successfully!
========================================
✅ VoiceScribe AI is ready!
🌐 Opening in browser...
========================================

Running on local URL:  http://127.0.0.1:7860
Running on public URL: https://xxxxx.gradio.live

To create a public link, set `share=True` in `launch()`.
```

---

## Testing the Installation

Run the main application to verify everything works:

```bash
python voicescribe_ai.py
```

This will load all models and launch the web interface. If it starts successfully, the installation is complete!

---

## Troubleshooting

### Issue: Import Error

**Error**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
```bash
pip install -r requirements.txt --force-reinstall
```

### Issue: Out of Memory

**Error**: `CUDA out of memory` or system freezing

**Solutions**:
1. Use smaller models - Edit [config.py](config.py):
   ```python
   WHISPER_MODEL = "openai/whisper-small.en"  # Instead of medium
   ```

2. Force CPU usage - Edit [config.py](config.py):
   ```python
   FORCE_CPU = True
   ```

3. Close other applications

4. Process shorter audio files (< 10 minutes)

### Issue: Slow Transcription

**Solutions**:
1. Enable GPU (see GPU Setup section)
2. Use smaller Whisper model
3. Check that CUDA is properly installed:
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```

### Issue: Models Not Downloading

**Error**: `ConnectionError` or download failures

**Solutions**:
1. Check internet connection
2. Set up HuggingFace cache manually:
   ```bash
   export HF_HOME=/path/to/cache  # macOS/Linux
   set HF_HOME=C:\path\to\cache   # Windows
   ```

3. Download models manually from [Hugging Face](https://huggingface.co/)

### Issue: Port Already in Use

**Error**: `OSError: [Errno 48] Address already in use`

**Solution**: Change port in [config.py](config.py):
```python
SERVER_PORT = 7861  # Or any available port
```

### Issue: Audio File Not Supported

**Solutions**:
1. Convert audio to MP3 or WAV format
2. Install ffmpeg:
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt-get install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

3. Install additional audio support:
   ```bash
   pip install pydub ffmpeg-python
   ```

---

## Updating

### Update VoiceScribe AI:

```bash
git pull  # If using git
pip install -r requirements.txt --upgrade
```

### Update Specific Package:

```bash
pip install --upgrade package-name
```

---

## Uninstalling

### Remove Virtual Environment:

```bash
deactivate  # Exit virtual environment
rm -rf venv  # macOS/Linux
rmdir /s venv  # Windows
```

### Remove Models Cache:

```bash
# Default HuggingFace cache location:
rm -rf ~/.cache/huggingface  # macOS/Linux
rmdir /s %USERPROFILE%\.cache\huggingface  # Windows
```

---

## System Requirements

### Minimum Requirements:
- CPU: Dual-core processor
- RAM: 8GB
- Storage: 10GB free space
- OS: Windows 10+, macOS 10.14+, Ubuntu 18.04+

### Recommended Requirements:
- CPU: Quad-core processor or better
- RAM: 16GB
- GPU: NVIDIA GPU with 4GB+ VRAM
- Storage: 20GB free space
- OS: Latest stable version

---

## Model Sizes

Default models will download approximately:

| Model | Size | Purpose |
|-------|------|---------|
| Whisper Medium | ~5GB | Transcription |
| BART Large CNN | ~1.5GB | Summarization |
| FLAN-T5 Base | ~900MB | Q&A |
| Sentence Transformers | ~90MB | Embeddings |
| **Total** | **~7.5GB** | |

You can reduce this by using smaller models in [config.py](config.py).

---

## Getting Help

If you encounter issues:

1. Check this installation guide
2. Read the main [README.md](README.md)
3. Search existing issues on GitHub
4. Create a new issue with:
   - Your OS and Python version
   - Complete error message
   - Steps to reproduce

---

## Next Steps

After successful installation:

1. Read the [README.md](README.md) for usage instructions
2. Check [config.py](config.py) for customization options
3. Try the example in the Jupyter notebook
4. Start transcribing your audio files!

---

**Happy Transcribing! 🎤**
