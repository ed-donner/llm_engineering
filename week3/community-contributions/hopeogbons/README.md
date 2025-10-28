# 🎙️ Audio Transcription Assistant

An AI-powered audio transcription tool that converts speech to text in multiple languages using OpenAI's Whisper model.

## Why I Built This

In today's content-driven world, audio and video are everywhere—podcasts, meetings, lectures, interviews. But what if you need to quickly extract text from an audio file in a different language? Or create searchable transcripts from recordings?

Manual transcription is time-consuming and expensive. I wanted to build something that could:

- Accept audio files in any format (MP3, WAV, etc.)
- Transcribe them accurately using AI
- Support multiple languages
- Work locally on my Mac **and** on cloud GPUs (Google Colab)

That's where **Whisper** comes in—OpenAI's powerful speech recognition model.

## Features

- 📤 **Upload any audio file** (MP3, WAV, M4A, FLAC, etc.)
- 🌍 **12+ languages supported** with auto-detection
- 🤖 **Accurate AI-powered transcription** using Whisper
- ⚡ **Cross-platform** - works on CPU (Mac) or GPU (Colab)
- 🎨 **Clean web interface** built with Gradio
- 🚀 **Fast processing** with optimized model settings

## Tech Stack

- **OpenAI Whisper** - Speech recognition model
- **Gradio** - Web interface framework
- **PyTorch** - Deep learning backend
- **NumPy** - Numerical computing
- **ffmpeg** - Audio file processing

## Installation

### Prerequisites

- Python 3.12+
- ffmpeg (for audio processing)
- uv package manager (or pip)

### Setup

1. Clone this repository or download the notebook

2. Install dependencies:

```bash
# Install compatible NumPy version
uv pip install --reinstall "numpy==1.26.4"

# Install PyTorch
uv pip install torch torchvision torchaudio

# Install Gradio and Whisper
uv pip install gradio openai-whisper ffmpeg-python

# (Optional) Install Ollama for LLM features
uv pip install ollama
```

3. **For Mac users**, ensure ffmpeg is installed:

```bash
brew install ffmpeg
```

## Usage

### Running Locally

1. Open the Jupyter notebook `week3 EXERCISE_hopeogbons.ipynb`

2. Run all cells in order:

   - Cell 1: Install dependencies
   - Cell 2: Import libraries
   - Cell 3: Load Whisper model
   - Cell 4: Define transcription function
   - Cell 5: Build Gradio interface
   - Cell 6: Launch the app

3. The app will automatically open in your browser

4. Upload an audio file, select the language, and click Submit!

### Running on Google Colab

For GPU acceleration:

1. Open the notebook in Google Colab
2. Runtime → Change runtime type → **GPU (T4)**
3. Run all cells in order
4. The model will automatically use GPU acceleration

**Note:** First run downloads the Whisper model (~140MB) - this is a one-time download.

## Supported Languages

- 🇬🇧 English
- 🇪🇸 Spanish
- 🇫🇷 French
- 🇩🇪 German
- 🇮🇹 Italian
- 🇵🇹 Portuguese
- 🇨🇳 Chinese
- 🇯🇵 Japanese
- 🇰🇷 Korean
- 🇷🇺 Russian
- 🇸🇦 Arabic
- 🌐 Auto-detect

## How It Works

1. **Upload** - User uploads an audio file through the Gradio interface
2. **Process** - ffmpeg decodes the audio file
3. **Transcribe** - Whisper model processes the audio and generates text
4. **Display** - Transcription is shown in the output box

The Whisper "base" model is used for a balance between speed and accuracy:

- Fast enough for real-time use on CPU
- Accurate enough for most transcription needs
- Small enough (~140MB) for quick downloads

## Example Transcriptions

The app successfully transcribed:

- English podcast episodes
- French language audio (detected and transcribed)
- Multi-speaker conversations
- Audio with background noise

## What I Learned

Building this transcription assistant taught me:

- **Audio processing** with ffmpeg and Whisper
- **Cross-platform compatibility** (Mac CPU vs Colab GPU)
- **Dependency management** (dealing with NumPy version conflicts!)
- **Async handling** in Jupyter notebooks with Gradio
- **Model optimization** (choosing the right Whisper model size)

The biggest challenge? Getting ffmpeg and NumPy to play nice together across different environments. But solving those issues made me understand the stack much better.

## Troubleshooting

### Common Issues

**1. "No module named 'whisper'" error**

- Make sure you've installed `openai-whisper`, not just `whisper`
- Restart your kernel after installation

**2. "ffmpeg not found" error**

- Install ffmpeg: `brew install ffmpeg` (Mac) or `apt-get install ffmpeg` (Linux)

**3. NumPy version conflicts**

- Use NumPy 1.26.4: `uv pip install --reinstall "numpy==1.26.4"`
- Restart kernel after reinstalling

**4. Gradio event loop errors**

- Use `prevent_thread_lock=True` in `app.launch()`
- Restart kernel if errors persist

## Future Enhancements

- [ ] Support for real-time audio streaming
- [ ] Speaker diarization (identifying different speakers)
- [ ] Export transcripts to multiple formats (SRT, VTT, TXT)
- [ ] Integration with LLMs for summarization
- [ ] Batch processing for multiple files

## Contributing

Feel free to fork this project and submit pull requests with improvements!

## License

This project is open source and available under the MIT License.

## Acknowledgments

- **OpenAI** for the amazing Whisper model
- **Gradio** team for the intuitive interface framework
- **Andela LLM Engineering Program** for the learning opportunity

---

**Built with ❤️ as part of the Andela LLM Engineering Program**

For questions or feedback, feel free to reach out!
