# Google Colab Link
https://colab.research.google.com/drive/1qbUrZr740xa_eN-Nud_nfjX2qTYA-p2_?usp=sharing

# Assistant Speaker Interview

A voice-based AI interview assistant system that conducts technical interviews for LLM Engineering positions. The system uses speech-to-text, AI conversation, and text-to-speech to create a natural voice interview experience.

## 🎯 Overview

This project implements an interactive voice interview system that:
- Records and transcribes your speech using Whisper
- Conducts a technical interview using OpenAI's GPT-4.1-mini
- Responds with natural-sounding speech using Kokoro TTS
- Provides a user-friendly Gradio interface for interaction

## ✨ Features

- **Speech Recognition**: Real-time speech-to-text using OpenAI Whisper (tiny model)
- **AI Interviewer**: Conducts technical interviews focused on LLM Engineering basics
- **Text-to-Speech**: Natural voice responses using Kokoro TTS pipeline
- **Interactive UI**: Gradio-based web interface for easy interaction
- **GPU Support**: Automatically uses GPU when available for faster processing

## 🛠️ Technologies Used

- **Speech-to-Text**: OpenAI Whisper (tiny model)
- **Text-to-Speech**: Kokoro TTS Pipeline
- **AI Model**: OpenAI GPT-4.1-mini
- **Interface**: Gradio
- **Audio Processing**: librosa, soundfile
- **Deep Learning**: PyTorch, Transformers

## 📋 Requirements

### Dependencies

- Python 3.8+
- PyTorch
- Transformers
- Gradio
- librosa
- soundfile
- numpy
- openai
- kokoro (>=0.9.2)
- espeak-ng (system package)

### API Keys Required

1. **Hugging Face Token** (`HF_TOKEN`): For accessing Kokoro TTS model
2. **OpenAI API Key** (`OPENAI_API_KEY`): For GPT-4.1-mini chat completions

## 🚀 Setup Instructions

### For Google Colab

1. **Upload the notebook** to Google Colab
2. **Set up API keys** in Colab secrets:
   - Go to the left sidebar → 🔑 Secrets
   - Add `HF_TOKEN` with your Hugging Face token
   - Add `OPENAI_API_KEY` with your OpenAI API key
3. **Run all cells** in sequence
4. **Access the interface** via the Gradio link provided

### For Local Setup

1. **Install dependencies**:
   ```bash
   pip install kokoro>=0.9.2 soundfile transformers torch gradio librosa openai numpy scipy
   sudo apt-get install espeak-ng  # For Linux
   ```

2. **Set up environment variables**:
   ```bash
   export HF_TOKEN="your_huggingface_token"
   export OPENAI_API_KEY="your_openai_api_key"
   ```

3. **Modify the notebook**:
   - Replace `google.colab.userdata` with environment variables:
     ```python
     import os
     hf_token = os.getenv('HF_TOKEN')
     openai.api_key = os.getenv('OPENAI_API_KEY')
     ```

4. **Run the notebook** or convert to Python script

## 📖 Usage

1. **Start the application**: Run all cells in the notebook
2. **Access the interface**: Click on the Gradio link or use the local URL
3. **Record your response**: Click the microphone button and speak your answer
4. **Listen to the response**: The AI interviewer will respond with voice
5. **Continue the interview**: The system maintains conversation history

### Interview Flow

- The interviewer asks **one question at a time**
- Questions focus on **basic LLM concepts, Transformers, Hugging Face, and Pipelines**
- Questions progressively increase in difficulty
- After **3 questions**, the interview concludes with feedback
- All responses are kept **under 60 words** for voice conversation

## 🎤 Interview System Details

### Interview Configuration

The system is configured as a **Technical Interviewer for Junior LLM Engineering positions**:

- **Topic Scope**: Basic LLM concepts, Transformers, Hugging Face, Pipelines
- **Excluded Topics**: RAG, Fine-Tuning
- **Question Format**: One question per turn, progressive difficulty
- **Response Length**: Under 60 words (optimized for voice)
- **Interview Length**: 3 questions total

### System Message

The AI uses a detailed system prompt that:
- Defines the interviewer role and expertise
- Sets question difficulty progression
- Enforces response length constraints
- Manages interview flow and completion

## 📁 Project Structure

```
assistant_speaker_interview.ipynb
├── Setup and Installation
│   ├── Install dependencies (kokoro, soundfile, espeak-ng)
│   └── Import libraries
├── Configuration
│   ├── Load API keys (HF_TOKEN, OPENAI_API_KEY)
│   └── Set model (GPT-4.1-mini)
├── Model Loading
│   ├── Whisper STT model (openai/whisper-tiny)
│   └── Kokoro TTS pipeline
├── Core Functions
│   ├── speech_to_text() - Transcribe audio to text
│   ├── text_to_speech() - Convert text to audio
│   └── chat() - Handle conversation with GPT
├── Main Pipeline
│   └── conversation_pipeline() - End-to-end voice conversation
└── Gradio Interface
    └── Launch interactive web interface
```

## ⚙️ Configuration

### Model Settings

- **Whisper Model**: `openai/whisper-tiny` (16kHz sampling rate)
- **TTS Model**: Kokoro-82M with language code 'a' (auto)
- **TTS Voice**: `af_heart`
- **Chat Model**: `gpt-4.1-mini`

### Customization

To modify the interview system message, edit the `sm_interview` variable in the notebook:

```python
sm_interview = """
  ROLE: You are an experienced Technical Interviewer...
  # Your custom prompt here
"""
```

## 🔧 Troubleshooting

### Common Issues

1. **API Key Errors**:
   - Ensure keys are set correctly in Colab secrets or environment variables
   - Verify keys have proper permissions

2. **Audio Issues**:
   - Check microphone permissions in browser
   - Ensure audio format is supported (WAV recommended)

3. **Model Loading Errors**:
   - Check internet connection for model downloads
   - Verify Hugging Face token has access to Kokoro model

4. **GPU Not Available**:
   - System will fall back to CPU (slower but functional)
   - For Colab: Enable GPU in Runtime settings

## 📝 Notes

- The system is optimized for **Google Colab** but can be adapted for local use
- Audio files are temporarily saved as `final_response.wav`
- Conversation history is maintained in the `history` list
- The Gradio interface automatically creates a shareable link in Colab

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📄 License

This project uses various open-source libraries. Please refer to their respective licenses:
- Whisper: MIT License
- Kokoro: Check Hugging Face model card
- Gradio: Apache 2.0
- OpenAI API: Subject to OpenAI's terms of service

## 🙏 Acknowledgments

- OpenAI for Whisper and GPT models
- Hugging Face for model hosting and Transformers library
- Kokoro TTS team for the text-to-speech model
- Gradio team for the interface framework

---

**Note**: This is an educational project for conducting voice-based technical interviews. Ensure you have proper API access and comply with all service terms of use.

