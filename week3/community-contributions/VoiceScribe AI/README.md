# 🎤 VoiceScribe AI

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Status](https://img.shields.io/badge/status-active-success)

**VoiceScribe AI** is an intelligent audio analysis tool that transforms your MP3 recordings into actionable insights. Upload audio files to get automatic transcription, concise summaries, key points extraction, and even chat directly with your transcript using AI-powered Q&A.

---

## 🔹 Key Features

| Feature | Description |
|---------|-------------|
| 🎤 **Automatic Transcription** | Converts audio to text in real-time using OpenAI's Whisper model |
| 🧠 **Smart Summarization** | Generates clear summaries and highlights key ideas using BART |
| 📌 **Key Points Extraction** | Automatically lists the main topics and action items |
| 🔍 **Searchable Transcript** | Quickly find parts of the recording by keyword |
| 💬 **Chat with Audio (Q&A Mode)** | Ask natural questions like "What did they say about training data?" using RAG |
| 📂 **Drag-and-Drop Uploads** | Simple, user-friendly Gradio interface |
| ⚡ **Real-Time Progress Bar** | Watch transcription progress as it happens |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- CUDA-compatible GPU (recommended for faster processing)
- 8GB+ RAM (16GB recommended)

### Installation

1. **Clone or download this repository**

```bash
cd "VoiceScribe AI"
```

2. **Create a virtual environment** (recommended)

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

### Running the Application

```bash
python voicescribe_ai.py
```

The application will:
- Load all AI models (this may take a few minutes on first run)
- Launch a web interface
- Open automatically in your default browser
- Provide a public URL for sharing (if `share=True`)

---

## 📖 Usage Guide

### 1️⃣ Transcribe & Analyze

1. Navigate to the **"Transcribe & Analyze"** tab
2. Click on the audio upload box or drag and drop your audio file
3. Click **"🚀 Transcribe & Analyze"**
4. Wait for processing (2-5 minutes depending on file length)
5. View your results:
   - **Full Transcript**: Complete text transcription
   - **Summary**: Concise overview of the content
   - **Key Points**: Main topics and action items

### 2️⃣ Chat with Audio (Q&A)

1. After transcribing your audio, go to the **"Chat with Audio"** tab
2. Type your question in natural language
3. Click **"🤔 Get Answer"**
4. The AI will search the transcript and provide relevant answers

**Example Questions:**
- "What were the main topics discussed?"
- "What did they say about the budget?"
- "What are the action items mentioned?"
- "Who were the speakers?"

### 3️⃣ Search Transcript

1. Go to the **"Search Transcript"** tab
2. Enter a keyword or phrase
3. Click **"🔎 Search"**
4. View all occurrences with context

---

## 🛠️ Technology Stack

### AI Models

| Component | Model | Purpose |
|-----------|-------|---------|
| **Transcription** | [OpenAI Whisper](https://github.com/openai/whisper) (medium.en) | Speech-to-text conversion |
| **Summarization** | [BART-large-CNN](https://huggingface.co/facebook/bart-large-cnn) | Text summarization |
| **Q&A** | [Google FLAN-T5](https://huggingface.co/google/flan-t5-base) | Question answering |
| **Embeddings** | [Sentence Transformers](https://www.sbert.net/) (all-MiniLM-L6-v2) | Vector embeddings |

### Frameworks

- **LangChain**: RAG (Retrieval Augmented Generation) framework
- **FAISS**: Vector database for efficient similarity search
- **Gradio**: Web UI framework
- **PyTorch**: Deep learning framework
- **Transformers**: Hugging Face model library

---

## 🎯 Use Cases

- **Meeting Minutes**: Automatically transcribe and summarize team meetings
- **Podcast Analysis**: Extract key insights from podcast episodes
- **Interview Transcription**: Convert interviews to searchable text
- **Lecture Notes**: Transcribe educational content and generate study notes
- **Research Interviews**: Analyze qualitative research data
- **Content Creation**: Extract quotes and key points for articles

---

## ⚙️ Configuration

### Model Selection

You can customize the models in `voicescribe_ai.py`:

```python
# Transcription model options:
# - "openai/whisper-tiny.en" (fastest, less accurate)
# - "openai/whisper-base.en"
# - "openai/whisper-small.en"
# - "openai/whisper-medium.en" (default, balanced)
# - "openai/whisper-large" (most accurate, slowest)

self.transcription_pipe = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-medium.en",  # Change here
    ...
)
```

### GPU vs CPU

The application automatically detects and uses GPU if available. To force CPU:

```python
self.device = 'cpu'  # Force CPU usage
```

### Vector Store

For GPU-accelerated vector search, install `faiss-gpu`:

```bash
pip uninstall faiss-cpu
pip install faiss-gpu
```

---

## 📊 Performance Tips

### For Faster Processing:
1. **Use GPU**: CUDA-compatible GPU significantly speeds up processing
2. **Smaller Models**: Use `whisper-small.en` or `whisper-base.en` for faster transcription
3. **Shorter Files**: Process files in smaller chunks (< 10 minutes each)

### For Better Accuracy:
1. **Larger Models**: Use `whisper-large` for best transcription quality
2. **Clean Audio**: Use high-quality audio with minimal background noise
3. **English Content**: Models are optimized for English (use multilingual models for other languages)

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: Out of memory error
- **Solution**: Use smaller models or process on CPU
- Reduce chunk size in RAG configuration

**Issue**: Slow transcription
- **Solution**:
  - Use GPU if available
  - Try smaller Whisper models
  - Close other applications

**Issue**: Models not downloading
- **Solution**: Check internet connection
- Manually download models from Hugging Face

**Issue**: Audio file not supported
- **Solution**: Convert to MP3 or WAV format
- Install `ffmpeg`: `pip install ffmpeg-python`

---

## 📁 Project Structure

```
VoiceScribe AI/
├── voicescribe_ai.py      # Main application
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── examples/              # Example audio files (optional)
```

---

## 🔮 Future Enhancements

- [ ] Multi-language support
- [ ] Speaker diarization (identify different speakers)
- [ ] Export to multiple formats (PDF, DOCX, JSON)
- [ ] Batch processing for multiple files
- [ ] Custom vocabulary for domain-specific terms
- [ ] Integration with cloud storage (Google Drive, Dropbox)
- [ ] Real-time transcription from microphone
- [ ] Sentiment analysis
- [ ] Named entity recognition (NER)

---

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📧 Contact & Support

For questions, issues, or suggestions:
- Open an issue on GitHub
- Email: [your-email@example.com]

---

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [Hugging Face](https://huggingface.co/) for model hosting
- [LangChain](https://www.langchain.com/) for RAG framework
- [Gradio](https://gradio.app/) for the UI framework

---

## ⭐ Star History

If you find this project useful, please consider giving it a star!

---

**Built with ❤️ using Open Source AI Models**
