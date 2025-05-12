# Airline AI Assistant

A sophisticated AI-powered airline assistant that leverages agent-based architecture and multi-modal capabilities to provide comprehensive customer support. This project combines multiple AI technologies, including language models, vision models, and audio processing, to create an intelligent assistant capable of handling complex customer queries through various interaction modes.

## Features

### Agent-Based Architecture
- **Multi-Agent System**: Utilizes specialized agents for different tasks:
  - Chat Agent: Handles conversation flow and context management
  - Translation Agent: Manages multilingual support with focus on Arabic
  - Vision Agent: Generates and processes visual responses
  - Audio Agent: Handles voice input and speech processing
- **Tool Integration**: Each agent has access to specialized tools:
  - Text Generation Tools (Ollama)
  - Translation Tools (Ollama)
  - Image Generation Tools (DALL-E)
  - Audio Processing Tools (Whisper)
- **Context Management**: Agents maintain conversation history and context for coherent interactions

### Multi-Modal Capabilities
- **Text Processing**:
  - Natural language understanding
  - Context-aware responses
  - Multi-language support
- **Visual Processing**:
  - Image generation based on context
  - Visual response to queries
  - Image-to-text understanding
- **Audio Processing**:
  - Voice-to-text conversion
  - Multi-format audio support
  - Real-time audio processing

### Core Features
- **Intelligent Chat Interface**: Context-aware conversations with memory
- **Arabic Translation**: Advanced translation capabilities with context preservation
- **Voice Interaction**: Natural voice input and processing
- **Visual Response Generation**: Contextual image generation
- **Multi-Tool Integration**: Seamless coordination between different AI tools

## Technical Architecture

### Agent System

<pre> ```
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Chat Agent │<────>│ Vision Agent │<────>│ Audio Agent │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
│ │ │
▼ ▼ ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Translation   │ │ Image         │ │ Audio         │
│ Tools         │ │ Generation    │ │ Processing    │
│ (Ollama)      │ │ (DALL-E)      │ │ (Whisper)     │
└───────────────┘ └───────────────┘ └───────────────┘
``` </pre>

### Multi-Modal Flow
1. **Input Processing**:
   - Text input → Chat Agent
   - Voice input → Audio Agent → Chat Agent
   - Image input → Vision Agent → Chat Agent

2. **Response Generation**:
   - Chat Agent coordinates with other agents
   - Translation Agent processes language needs
   - Vision Agent generates visual responses
   - Audio Agent processes voice output

## Prerequisites

Before running the application, ensure you have the following installed:

- Python 3.8 or higher
- Ollama (for local LLM support)
- FFmpeg (for audio processing)
- Required Python packages (listed in requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/airline_ai_assistant.git
cd airline_ai_assistant
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
```bash
# Create a .env file with your API keys
OPENAI_API_KEY=your_key_here
```

## Usage

1. Start the application:
```bash
python main.py
```

2. Access the web interface through your browser (default: http://localhost:7860)

3. Interact with the assistant:
   - Type your message in the text box
   - Use the microphone for voice input
   - View responses in both English and Arabic
   - See visual representations of responses

## Project Structure

<pre> ```
airline_ai_assistant/
├── main.py # Main application file with agent orchestration
├── agents/ # Agent implementations
│ ├── chat_agent.py # Chat handling agent
│ ├── vision_agent.py # Visual processing agent
│ ├── audio_agent.py # Audio processing agent
│ └── translation_agent.py # Translation handling agent
├── tools/ # Tool implementations
│ ├── text_tools.py # Text processing tools
│ ├── vision_tools.py # Image processing tools
│ └── audio_tools.py # Audio processing tools
├── requirements.txt # Python dependencies
├── .env # Environment variables
└── README.md # Project documentation
``` </pre>

## Key Components

### Agent System
- **Chat Agent**: Manages conversation flow and context
- **Translation Agent**: Handles multilingual support
- **Vision Agent**: Processes visual content
- **Audio Agent**: Manages voice interactions

### Tool Integration
- **Text Tools**: Language model integration
- **Vision Tools**: Image generation and processing
- **Audio Tools**: Voice processing and transcription

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for the Whisper and DALL-E models
- Ollama for local LLM support
- Gradio for the web interface
- The open-source community for various tools and libraries

## Contact

For questions or support, please open an issue in the repository.