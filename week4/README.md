---
title: Python to C++ Code Optimizer
emoji: 🚀
colorFrom: purple
colorTo: blue
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# 🚀 Python to C++ Code Optimizer

An AI-powered tool that converts Python code to high-performance C++ using GPT-4o and Claude-3.5-Sonnet.

## 🎯 What It Does

This application takes Python code as input and uses frontier AI models to automatically convert it to optimized C++ code. It then allows you to:

- Compare the generated C++ code side-by-side with the original Python
- Execute both versions and compare performance
- See real-world speedups (typically 10-100x faster)

## 🔐 Password Protection

This Space is password-protected. To access:

1. **Username:** `user`
2. **Password:** Contact the Space owner for the password

The password helps limit access while keeping the Space publicly discoverable.

## ⚠️ Security Warning

**IMPORTANT**: This application executes arbitrary code (both Python and C++). 

- Only run code from trusted sources
- Malicious code can harm the system
- Use at your own risk
- Not recommended for production use without proper sandboxing

## 🔧 Setup Instructions

### For Hugging Face Spaces

1. Fork or duplicate this Space
2. Go to **Settings** → **Repository secrets**
3. Add the following secrets:
   - `OPENAI_API_KEY` - Your OpenAI API key from https://platform.openai.com/api-keys
   - `ANTHROPIC_API_KEY` - Your Anthropic API key from https://console.anthropic.com/
   - `APP_PASSWORD` - Your chosen password for accessing the app (e.g., `mySecurePass123`)

### For Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set environment variables:
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   ```
4. Run the app:
   ```bash
   python app.py
   ```

### For C++ Compilation

The app requires a C++ compiler:
- **Linux**: `g++` (usually pre-installed)
- **macOS**: Install Xcode Command Line Tools
- **Windows**: Install MinGW or use WSL

The default compilation command uses `g++`. You may need to adjust the compiler flags in `app.py` for your platform.

## 🎓 Educational Use

This project is designed for educational purposes to demonstrate:
- AI-powered code generation and optimization
- Performance differences between Python and C++
- Real-time streaming from AI models
- Interactive code execution environments

## 📊 Example Performance

**Pi Calculation (100M iterations):**
- Python: ~6.3 seconds
- C++ (optimized): ~0.6 seconds
- **Speedup: ~10x**

**Maximum Subarray (10K elements, 20 runs):**
- Python: ~45 seconds
- C++ (optimized): ~0.4 seconds
- **Speedup: ~110x**

## 🛡️ Safety Features

- Execution timeouts (30 seconds)
- Error handling for compilation failures
- Clear security warnings in UI
- Sandboxed execution recommended for production

## 📝 Model Options

Choose between two frontier models:

1. **GPT-4o** (OpenAI)
   - Excellent at code generation
   - Good optimization strategies
   - Fast streaming responses

2. **Claude-3.5-Sonnet** (Anthropic)
   - Strong code understanding
   - Detailed optimization
   - High-quality output

## 💰 Cost Considerations

Both models are paid APIs:
- GPT-4o: ~$5 per million input tokens
- Claude-3.5-Sonnet: ~$3 per million input tokens

For ultra-low cost, modify the code to use:
- `gpt-4o-mini` (20x cheaper)
- `claude-3-haiku` (15x cheaper)

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License - feel free to use and modify as needed.

## ⚡ Credits

Created as part of an LLM Engineering course demonstrating practical applications of frontier AI models.

## 🔗 Resources

- [OpenAI Platform](https://platform.openai.com/)
- [Anthropic Console](https://console.anthropic.com/)
- [Gradio Documentation](https://www.gradio.app/docs/)
- [C++ Performance Optimization](https://en.cppreference.com/)

---

**Disclaimer**: This tool is for educational and research purposes. Always review generated code before using in production. The developers assume no liability for damages caused by code execution.

