# Configuration Guide

## Environment Variables

Create a `.env` file in the root directory:

```bash
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
GROQ_API_KEY=your_groq_key_here
PORT=7860  # Optional, default port for the web interface
```

## Model Configuration

Model names are configured in `src/ai_code_converter/config.py`:

```python
# Model configurations
OPENAI_MODEL = "gpt-4o-mini"              # OpenAI model name
CLAUDE_MODEL = "claude-3-sonnet-20240307" # Anthropic Claude model
DEEPSEEK_MODEL = "deepseek-chat"          # DeepSeek model
GEMINI_MODEL = "gemini-1.5-flash"         # Google Gemini model
GROQ_MODEL = "llama3-70b-8192"            # GROQ model
```

You can modify these values to use different model versions based on your requirements and API access.

## Prerequisites

The following dependencies are required for full functionality:

- Python 3.10+
- Node.js and npm (with TypeScript)
- Java JDK 17+
- Julia 1.9+
- Go 1.21+
- GCC/G++
- Perl
- Lua 5.3+
- PHP
- R
- Ruby
- Rust (rustc and cargo)
- Mono (for C#)
- Swift 5.9+
- Kotlin
- SQLite3

Using Docker is recommended as it includes all necessary dependencies.

## Docker Configuration

The application includes Docker support for easy deployment. The `docker-compose.yml` file defines the service configuration:

```yaml
version: '3'
services:
  ai_code_converter:
    build: .
    ports:
      - "${PORT:-7860}:7860"
    volumes:
      - ./logs:/app/logs
    env_file:
      - .env
    restart: unless-stopped
```

You can customize the port mapping and volume mounts as needed.

## Application Settings

Additional application settings can be configured in `src/ai_code_converter/config.py`:

- UI theme and styling
- Default language selections
- Model temperature settings
- Execution timeouts
- Logging configuration
