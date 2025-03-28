# Project Structure

This document provides an overview of the CodeXchange AI project structure and architecture.

For a visual representation of the application architecture and component relationships, please refer to the [Architecture Diagram](./architecture_diagram.md).

## Directory Structure

```
ai_code_converter/
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
├── run.py                  # Application entry point
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── .env.example            # Environment variables template
├── docs/                   # Detailed documentation
└── src/                    # Source code directory
    └── ai_code_converter/
        ├── main.py         # Main application logic
        ├── app.py          # Gradio interface setup
        ├── config.py       # Model and app configuration
        ├── template.j2     # Prompt template
        ├── core/           # Core functionality
        │   ├── __init__.py
        │   ├── language_detection.py  # Language validation
        │   └── code_execution.py      # Code execution
        ├── models/         # AI model integration
        │   ├── __init__.py
        │   └── ai_streaming.py        # API clients and streaming
        └── utils/          # Utility functions
            ├── __init__.py
            └── logging.py             # Logging configuration
```

## Component Descriptions

### Entry Points

- **run.py**: The main entry point for the application. It imports and initializes the necessary modules and starts the application.

- **main.py**: Contains the main application logic, initializes the application components, and starts the Gradio interface.

### Core Components

- **app.py**: Sets up the Gradio interface and defines UI components. Contains the `CodeConverterApp` class that handles the UI and code conversion logic.

- **config.py**: Contains configuration for models, languages, and application settings. Defines supported languages, model names, and UI styling.

- **template.j2**: A Jinja2 template used to create prompts for the LLMs with language-specific instructions for code conversion.

### Core Directory

The `core` directory contains modules for core functionality:

- **language_detection.py**: Contains the `LanguageDetector` class with static methods to validate if code matches the expected language patterns.

- **code_execution.py**: Handles the execution of code in different programming languages. Contains language-specific execution methods.

### Models Directory

The `models` directory contains modules for AI model integration:

- **ai_streaming.py**: Handles API calls to various LLMs (GPT, Claude, Gemini, DeepSeek, GROQ). Contains methods for streaming responses from different AI providers.

### Utils Directory

The `utils` directory contains utility modules:

- **logging.py**: Configures the logging system for the application. Sets up console and file handlers with appropriate formatting.

## Application Flow

1. **Initialization**:
   - `run.py` imports the main module
   - `main.py` initializes the application components
   - `app.py` sets up the Gradio interface

2. **User Interaction**:
   - User selects source and target languages
   - User enters or uploads source code
   - User selects AI model and temperature
   - User clicks "Convert"

3. **Code Conversion**:
   - Source language is validated using `language_detection.py`
   - Prompt is created using `template.j2`
   - AI model is called using `ai_streaming.py`
   - Response is streamed back to the UI

4. **Code Execution** (optional):
   - User clicks "Run" on original or converted code
   - Code is executed using appropriate method in `code_execution.py`
   - Output is displayed in the UI

## Design Patterns

- **Singleton Pattern**: Used for API clients to ensure only one instance exists
- **Factory Pattern**: Used for creating language-specific execution methods
- **Strategy Pattern**: Used for selecting the appropriate AI model
- **Observer Pattern**: Used for streaming responses from AI models

## Dependencies

- **Gradio**: Web interface framework
- **Jinja2**: Template engine for creating prompts
- **OpenAI, Anthropic, Google, DeepSeek, GROQ APIs**: AI model providers
- **Various language interpreters and compilers**: For code execution
