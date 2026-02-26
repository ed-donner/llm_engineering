# Week 1 Exercise - Technical Question Explainer

**Author:** Samuel Kalu  
**Group:** Euclid  
**Bootcamp:** Andela Bootcamp  
**Date:** February 2026

## 📋 Description

A technical question explainer tool that demonstrates familiarity with both OpenAI API and Ollama (local LLM). This educational tool helps you understand complex technical concepts by providing detailed explanations from multiple AI models.

## ✨ Features

- **🎯 Dual Model Support**: Get explanations from both GPT-4o-mini (Frontier) and Llama 3.2 (Open-source)
- **📡 Streaming Responses**: Watch responses appear in real-time with proper Markdown formatting
- **💬 Interactive Mode**: Enter questions dynamically at runtime
- **📝 Clean Documentation**: Well-commented code with educational explanations
- **💾 Save Functionality**: Optionally save explanations to a markdown file for future reference
- **🔧 Modular Design**: Easy to extend with additional models or features

## 🎯 Learning Objectives Demonstrated

1. ✅ Working with OpenAI API (GPT-4o-mini)
2. ✅ Using Ollama for local LLM inference (Llama 3.2)
3. ✅ Streaming responses with proper formatting
4. ✅ Building reusable, modular code structure
5. ✅ Environment variable management with dotenv
6. ✅ Jupyter notebook best practices

## 📁 Files

- `week1_EXERCISE.ipynb` - Main Jupyter notebook with the complete implementation

## 🚀 Usage

### Prerequisites

1. **OpenAI API Key**: Set up in your `.env` file
2. **Ollama**: Installed and running locally with `llama3.2` model
3. **Python Environment**: All dependencies from the main `pyproject.toml`

### Quick Start

1. **Setup Environment**
   ```bash
   # Make sure Ollama is running
   ollama serve
   
   # In another terminal, pull the model (first time only)
   ollama pull llama3.2
   ```

2. **Configure API Keys**
   ```bash
   # Create a .env file in the project root
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Run the Notebook**
   - Open `week1_EXERCISE.ipynb` in Jupyter Lab or Cursor
   - Execute cells from top to bottom using `Shift + Enter`
   - Modify the `question` variable to ask your own technical questions

### Interactive Mode

To enable interactive input, uncomment line in Cell 5:
```python
question = input("Please enter your technical question: ")
```

### Example Questions

Try these technical questions to see the tool in action:

```python
# Python concepts
"Explain the difference between deep copy and shallow copy"

# Code analysis
"What does this decorator do? @functools.lru_cache(maxsize=None)"

# Data structures
"Explain how a hash map works and its time complexity"

# LLM concepts
"What is the attention mechanism in transformers?"
```

## 🏗️ Architecture

```
┌─────────────────┐
│  User Question  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  System Prompt  │  →  Educational tone & structure
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────┐
│  GPT-4  │ │ Llama 3  │
│  Mini   │ │   3.2    │
└────┬────┘ └────┬─────┘
     │           │
     └─────┬─────┘
           │
           ▼
┌─────────────────┐
│  Comparison &   │
│  Key Takeaways  │
└─────────────────┘
```

## 📊 Sample Output

### Input Question:
```
Please explain what this code does and why:
yield from {book.get("author") for book in books if book.get("author")}
```

### What You'll Learn:
- **Set comprehension** - Creating sets with unique values
- **`yield from`** - Generator delegation syntax
- **Defensive programming** - Using `.get()` to prevent errors
- **Filtering** - Removing None values with conditional

## 🔧 Customization Ideas

Make this tool your own:

1. **Add More Models**: Integrate Gemini, Claude, or Groq APIs
2. **Build a UI**: Create a Gradio interface (Week 2 material)
3. **Response Comparison**: Add automatic evaluation of which explanation is better
4. **Topic Specialization**: Customize system prompt for specific domains
5. **Batch Processing**: Process multiple questions at once
6. **Export Options**: Save to PDF, HTML, or shareable formats

## 🎓 Key Learnings

Through building this project, I gained:

- **Hands-on experience** with both commercial and open-source LLMs
- **Understanding of streaming** responses for better UX
- **Prompt engineering** skills for consistent, educational outputs
- **Code organization** for maintainable, reusable projects
- **Jupyter notebook** best practices for experimentation

## 📝 Requirements

- Python 3.11+
- OpenAI API key (optional - can use Ollama only)
- Ollama with llama3.2 model installed
- Dependencies from main `pyproject.toml`:
  - `openai`
  - `ollama`
  - `python-dotenv`
  - `ipywidgets` (for Jupyter display)

## 🐛 Troubleshooting

### Ollama Connection Error
```bash
# Make sure Ollama is running
ollama serve

# Check if model is downloaded
ollama list
# If not, pull it:
ollama pull llama3.2
```

### OpenAI API Error
```bash
# Verify your API key is set
echo $OPENAI_API_KEY  # Mac/Linux
echo %OPENAI_API_KEY%  # Windows

# Check your API key at https://platform.openai.com/api-keys
```

## 📚 References

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Ollama Documentation](https://ollama.com/)
- [Week 1 Course Material](../../day1.ipynb)
- [Official Exercise](../../week1%20EXERCISE.ipynb)

## 🙏 Acknowledgments

- **Instructor**: Edward Donner for the excellent LLM Engineering course
- **Community**: Fellow students whose contributions inspired this work
- **Open Source**: The amazing open-source AI community

---

**Happy Learning! 🚀**

*Feel free to reach out if you have questions or suggestions for improvement.*
