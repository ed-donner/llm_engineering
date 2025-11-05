# Code Explainer - LLM Engineering Week 1

An AI-powered code explanation tool using Llama 3.2 via Ollama.

## 🎯 Project Overview

This project demonstrates prompt engineering and local LLM integration by building a code explanation assistant. The tool analyzes code snippets and provides beginner-friendly, line-by-line explanations.

## ✨ Features

- **Local LLM Integration**: Uses Ollama with Llama 3.2 (no API costs!)
- **Two Modes of Operation**:
  - 📓 **Notebook Mode**: Interactive Jupyter notebook with rich Markdown display
  - 💻 **Terminal Mode**: Interactive CLI for continuous code explanation
- **Smart Explanations**: 
  - Summarizes overall purpose
  - Line-by-line breakdown
  - Highlights key programming concepts
  - Beginner-friendly language
- **Multiple Examples**: Loops, list comprehensions, OOP, recursion, decorators
- **Streaming Responses**: Real-time output as the model generates

## 🛠️ Technologies Used

- **Ollama**: Local LLM runtime
- **Llama 3.2**: Meta's language model
- **OpenAI Python SDK**: API-compatible interface
- **IPython**: Rich markdown display
- **python-dotenv**: Environment management

## 📋 Prerequisites

1. **Ollama installed** - Download from [ollama.com](https://ollama.com)
2. **Python 3.8+**
3. **Llama 3.2 model pulled**:
   ```bash
   ollama pull llama3.2
   ```

## 🚀 Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd llm-engineering/week1/my-solutions
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. (Optional) Configure environment
```bash
cp .env.example .env
# Edit .env if needed
```

## 💡 Usage

### Notebook Mode

1. Open `day1-solution.ipynb` in Jupyter or VS Code
2. Run cells sequentially
3. Use `explain_code_interactive()` function with your own code

```python
explain_code_interactive("""
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
""")
```

### Terminal Mode

```bash
python code_explainer.py
```

Then:
- Paste your code
- Press Enter twice (empty line)
- Get explanation!

**Commands:**
- `quit` / `exit` / `q` - Exit
- `clear` - Start fresh
- `examples` - See sample code snippets

## 🎓 Why Ollama?

I chose Ollama over OpenAI API for this project because:

✅ **No API Costs**: Completely free to use  
✅ **Privacy**: All data stays local  
✅ **Offline**: Works without internet  
✅ **Learning**: Hands-on experience with local LLM deployment  
✅ **Speed**: Fast responses on local hardware  

## 📝 Examples Included

1. **Recursion** - Fibonacci sequence
2. **Loops** - Simple iteration
3. **List Comprehensions** - Filtering and mapping
4. **Object-Oriented Programming** - Classes and methods
5. **Decorators** - Advanced Python concepts

## 🔧 Customization

### Change the model
Edit `code_explainer.py`:
```python
explainer = CodeExplainer(model="llama3.2:3b")  # Use smaller model
```

### Adjust temperature
Lower temperature = more consistent, Higher = more creative:
```python
temperature=0.3  # Current setting for code explanations
```

### Modify system prompt
Customize how the model explains code in the `system_prompt` variable.

## 🤝 Contributing

This is a course assignment, but feel free to fork and improve!

## 📄 License

MIT License - feel free to use for learning purposes.

## 👤 Author

İrem İrem  
LLM Engineering Course - Week 1 Assignment

## 🙏 Acknowledgments

- **Ed Donner** - Course instructor for the excellent LLM Engineering course
- **Anthropic** - For Ollama framework
- **Meta** - For Llama 3.2 model
