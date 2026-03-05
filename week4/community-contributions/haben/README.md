# Multi-Language Code Converter

AI-powered code translation tool that converts code between 13+ programming languages using state-of-the-art LLM models. Supports both frontier models (GPT-5, Claude 4.5, Gemini 2.5 Pro, Grok 4) and open-source alternatives (Ollama, Groq, OpenRouter).

## Features

- **Multi-language support**: Python, C++, Rust, Java, JavaScript, TypeScript, C, C#, Go, PHP, Swift, Ruby, Kotlin, Julia
- **Multi-LLM support**: OpenAI, Anthropic, Google, Grok, Ollama, Groq, OpenRouter
- **Performance optimization**: Generates optimized code for target language with system-specific tuning
- **Interactive interface**: Gradio-based web UI for code conversion
- **Compilation testing**: Automatic compilation and execution for compiled languages (C++, Rust, Go, C)

## Supported Models

**Frontier Models**: GPT-5, Claude Sonnet 4.5, Gemini 2.5 Pro, Grok 4  
**Open-Source Models**: Qwen2.5 Coder, DeepSeek Coder v2, GPT-OSS 20B/120B, Qwen3 Coder 30B

## Prerequisites

- Python 3.12+
- `uv` package manager (or `pip`)
- At least one API key:
  - **OpenRouter** (recommended): `OPENROUTER_API_KEY` + `OPENROUTER_BASE_URL`
  - **OpenAI**: `OPENAI_API_KEY` (direct access)
  - Optional: Anthropic, Google, Grok, Groq API keys for additional models
- Compilers (optional): `clang++`, `rustc`, `go`, `clang` for compilation testing

## Installation

1. **Configure environment variables** in `.env` at project root (`llm_engineering/.env`):

```bash
# Recommended: OpenRouter (provides OpenAI access)
OPENROUTER_API_KEY=sk-or-your-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Alternative: Direct OpenAI
# OPENAI_API_KEY=sk-your-openai-key-here

# Optional: Additional providers
# ANTHROPIC_API_KEY=sk-ant-your-key-here
# GOOGLE_API_KEY=your-google-api-key-here
# GROK_API_KEY=xai-your-key-here
# GROQ_API_KEY=gsk_your-key-here
```

**Note**: The notebook automatically loads `.env` from the root directory. OpenAI API access priority: OpenRouter → Direct OpenAI → None.

2. **Install dependencies**:

```bash
uv add openai python-dotenv gradio
```

3. **Ollama setup** (optional, for local models):

```bash
ollama pull qwen2.5-coder deepseek-coder gpt-oss:20b
```

## Usage

1. Open the notebook:
   ```bash
   jupyter notebook multi_language_code_converter.ipynb
   ```

2. Run all cells sequentially

3. The Gradio interface launches automatically. Use it to:
   - Select source and target languages
   - Choose an LLM model
   - Input source code
   - Add optional instructions
   - Enable compilation testing (for compiled languages)

## Architecture

```
Source Code → LLM Model → Converted Code → [Compilation] → Execution Results
```

The tool uses system information to optimize code generation for the target platform.

## Compilation Support

Automatic compilation and execution for:
- **C++**: `clang++` with `-Ofast -mcpu=native` optimization
- **Rust**: `rustc -O`
- **Go**: `go build`
- **C**: `clang` with optimization flags

For other languages, use online compilers (e.g., [Programiz](https://www.programiz.com/cpp-programming/online-compiler/)).

## Performance

Based on benchmark tests (Python to C++ conversion):
- Gemini 2.5 Pro: 1440x speedup
- Grok 4: 1060x speedup
- GPT-OSS 20B: 238x speedup
- GPT-5: 233x speedup
- Claude Sonnet 4.5: 184x speedup

## Technical Details

- **Language**: Python 3.12+
- **Dependencies**: OpenAI SDK, Gradio, python-dotenv
- **Type Safety**: Handles type conversions and overflow prevention
- **Error Handling**: Comprehensive error handling with clear messages
- **Code Quality**: Type hints, docstrings, and structured error handling

## Notes

- **Cost**: Frontier models provide better results but are more expensive. Use Ollama for cost-free local development.
- **Compilation**: Only available for languages with installed compilers. Other languages require online compilers.
- **System Info**: Automatically detects and uses system information for code optimization.

## Contributing

This project was created as part of the **Andela AI Engineering Bootcamp**, led by **ED Donner**.

## License

Part of the Andela AI Engineering Bootcamp curriculum.

---

**Built as part of the Andela AI Engineering Bootcamp**
