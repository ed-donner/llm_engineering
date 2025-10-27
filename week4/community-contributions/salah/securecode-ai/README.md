# SecureCode AI

**AI-Powered Code Security & Performance Analyzer**

Built for Week 4 of the LLM Engineering course - A novel solution that addresses real-world needs not covered by other community contributions.

## Why SecureCode AI?

Unlike other Week 4 projects that focus on docstrings or code conversion, **SecureCode AI** provides:

✅ **Security vulnerability detection** (OWASP Top 10)
✅ **Performance bottleneck analysis** (Big-O, complexity)
✅ **Automated fix generation** with explanations
✅ **Unit test generation** (happy path + edge cases)
✅ **Educational focus** - teaches WHY code is vulnerable/slow

Perfect for developers learning secure coding practices and performance optimization!

## Features

### 🔒 Security Analysis
Detects real vulnerabilities following OWASP guidelines:
- SQL Injection, XSS, Command Injection
- Path Traversal, Insecure Deserialization
- Hardcoded Credentials, Cryptographic Failures
- Authentication/Authorization Issues

### ⚡ Performance Analysis
Identifies performance issues:
- Time/Space Complexity (Big-O analysis)
- Inefficient Algorithms (nested loops, N+1 queries)
- Memory Leaks, Caching Opportunities
- Blocking I/O Operations

### 🔧 Auto-Fix Generation
Automatically generates:
- Secure code alternatives
- Optimized implementations
- Line-by-line explanations
- Best practice recommendations

### 🧪 Unit Test Generation
Creates comprehensive test suites:
- pytest/unittest compatible
- Happy path, edge cases, error handling
- Parameterized tests
- Test fixtures and mocks

### 🌍 Multi-Language Support
Python, JavaScript, Java, C++, Go, Rust with auto-detection

### 🤖 Model Agnostic
Works with any OpenRouter model - free tier available!

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

### TL;DR - 2 Steps to Run (using uvx)

```bash
# 1. Configure (get free API key from openrouter.ai)
cd week4/securecode-ai
cp .env.example .env
# Edit .env and add: OPENROUTER_API_KEY=your-key-here

# 2. Run (uvx handles everything else!)
./run.sh

# Or run manually:
# uvx --with gradio --with openai --with python-dotenv python main.py
```

**That's it!** No installation needed - `uvx` handles all dependencies automatically.

The Gradio interface opens automatically at `http://localhost:7860`

**First Time?** The default model is **FREE** - no credit card needed!

## Usage

### Security Analysis

1. Go to the "🔒 Security Analysis" tab
2. Paste your code
3. Select language (or use Auto-detect)
4. Click "🔍 Analyze Security"
5. Review the identified vulnerabilities

### Performance Analysis

1. Go to the "⚡ Performance Analysis" tab
2. Paste your code
3. Select language (or use Auto-detect)
4. Click "🚀 Analyze Performance"
5. Review performance issues and optimization suggestions

### Generate Fix

1. Go to the "🔧 Generate Fix" tab
2. Paste your original code
3. Paste the analysis report (from Security or Performance tab)
4. Select language (or use Auto-detect)
5. Click "✨ Generate Fix"
6. Review the fixed code and explanations

### Generate Tests

1. Go to the "🧪 Generate Tests" tab
2. Paste your code (functions or classes)
3. Select language (or use Auto-detect)
4. Click "🧪 Generate Tests"
5. Get complete pytest test file with:
   - Happy path tests
   - Edge cases
   - Error handling tests
   - Test fixtures if needed

## Example Code

Try the example code in `examples/`:
- `vulnerable_code.py` - Code with security issues
- `slow_code.py` - Code with performance issues
- `sample_functions.py` - Clean functions for test generation

## Configuration

### Changing Models

Edit `.env` to use different models:

```bash
# Free tier models (recommended for testing)
SECURECODE_MODEL=meta-llama/llama-3.1-8b-instruct:free
SECURECODE_MODEL=google/gemini-2.0-flash-exp:free

# Paid models (better quality)
SECURECODE_MODEL=openai/gpt-4o-mini
SECURECODE_MODEL=anthropic/claude-3.5-sonnet
SECURECODE_MODEL=qwen/qwen-2.5-coder-32b-instruct
```

Browse all available models at: https://openrouter.ai/models

## Project Structure

Clean, modular Python architecture following best practices:

```
securecode-ai/
├── src/securecode/              # Main package
│   ├── analyzers/               # Analysis engines
│   │   ├── base_analyzer.py         # Base class with OpenRouter client
│   │   ├── security_analyzer.py     # OWASP security analysis
│   │   ├── performance_analyzer.py  # Performance profiling
│   │   ├── fix_generator.py         # Auto-fix generation
│   │   └── test_generator.py        # Unit test creation
│   ├── prompts/                 # Specialized AI prompts
│   │   ├── security_prompts.py      # Security expert persona
│   │   ├── performance_prompts.py   # Performance engineer persona
│   │   ├── fix_prompts.py           # Code fixing prompts
│   │   └── test_prompts.py          # Test generation prompts
│   ├── utils/
│   │   └── language_detector.py     # Auto-detect code language
│   ├── config.py                # Environment config
│   └── app.py                   # Gradio UI (4 tabs)
├── examples/                    # Test code samples
│   ├── vulnerable_code.py           # SQL injection, etc.
│   ├── slow_code.py                 # O(n²) algorithms
│   └── sample_functions.py          # Clean code for testing
├── main.py                      # Application entry point
├── pyproject.toml              # Modern Python packaging
├── .env.example                # Configuration template
├── setup.sh                    # Automated setup script
├── QUICKSTART.md              # Detailed setup guide
└── README.md                   # This file
```

**Design Principles:**
- **Separation of Concerns**: Each analyzer is independent
- **DRY**: Base class handles OpenRouter communication
- **Extensible**: Easy to add new analyzers
- **Clean Code**: Type hints, docstrings, descriptive names

## Development

### Install development dependencies

```bash
pip install -e ".[dev]"
```

### Code formatting

```bash
black src/
ruff check src/
```

### Running tests

```bash
pytest
```

## How It Works

### Architecture

```
User Code → Language Detection → Specialized Prompt → OpenRouter API → AI Model
                                                                           ↓
User Interface ← Streaming Response ← Analysis/Fix/Tests ← Model Response
```

### Technical Implementation

1. **Multi-Analyzer Pattern**: Separate classes for security, performance, fixes, and tests
2. **Specialized Prompts**: Each analyzer uses persona-based prompts (security expert, performance engineer, etc.)
3. **Streaming Responses**: Real-time output using Gradio's streaming capabilities
4. **Model Agnostic**: Works with any OpenAI-compatible API through OpenRouter
5. **Clean Code**: Type hints, docstrings, modular design

### Example: Security Analysis Flow

```python
# User pastes code
code = "query = f'SELECT * FROM users WHERE id = {user_id}'"

# Security analyzer builds prompt
prompt = SecurityPrompt(code, language="Python")

# Calls AI model via OpenRouter
response = openai.chat.completions.create(
    model="meta-llama/llama-3.1-8b-instruct:free",
    messages=[
        {"role": "system", "content": SECURITY_EXPERT_PROMPT},
        {"role": "user", "content": code}
    ],
    stream=True
)

# Streams results to UI
for chunk in response:
    yield chunk  # Real-time display
```

## Cost Considerations

- **Free Tier Models**: Use models with `:free` suffix (rate-limited but no cost)
- **Paid Models**: More accurate but incur API costs (~$0.001-0.01 per analysis)
- **Recommended**: Start with `meta-llama/llama-3.1-8b-instruct:free` for testing

## Limitations

- Analysis quality depends on the AI model used
- Not a replacement for professional security audits
- May produce false positives or miss subtle issues
- Always review AI suggestions before applying to production

## Support

For issues or questions, open an issue in the repository.

## License

MIT License - See LICENSE file for details

## Week 4 Learning Objectives Met

This project demonstrates mastery of all Week 4 skills:

✅ **Multi-Model Integration** - Works with OpenAI, Anthropic, Google, Meta models
✅ **Prompt Engineering** - Specialized prompts for different analysis types
✅ **Code Analysis & Generation** - Security, performance, fixes, tests
✅ **Gradio UI Development** - Multi-tab interface with streaming
✅ **Real-World Application** - Addresses genuine developer needs
✅ **Clean Architecture** - Modular, extensible, well-documented

## What Makes This Novel?

Compared to other Week 4 community contributions:

| Feature | Other Projects | SecureCode AI |
|---------|----------------|---------------|
| Docstring Generation | ✅ (Many) | ➖ |
| Code Conversion | ✅ (Many) | ➖ |
| **Security Analysis** | ❌ None | ✅ **Unique** |
| **Performance Profiling** | ❌ None | ✅ **Unique** |
| **Educational Focus** | ❌ Limited | ✅ **Unique** |
| Unit Test Generation | ✅ (Some) | ✅ Enhanced |
| Auto-Fix with Explanation | ❌ None | ✅ **Unique** |

**Result**: A production-ready tool that teaches secure coding while solving real problems!

## Acknowledgments

- **LLM Engineering Course** by Edward Donner
- **OpenRouter** for multi-model API access
- **Gradio** for the excellent UI framework
- **OWASP** for security guidelines
- **Community** for inspiration from Week 4 contributions

## Contributing

Ideas for enhancements:
- Add more security rules (SANS Top 25, CWE)
- Implement batch file processing
- CI/CD integration (GitHub Actions)
- VSCode extension
- API endpoint for programmatic access
- Support for more languages

## License

MIT License - See LICENSE file for details

---

**Built with ❤️ for developers who care about security and performance**
