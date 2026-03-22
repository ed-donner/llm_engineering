# 🔶 Multi-Language Code Complexity Annotator

An automated tool that analyzes source code and annotates it with Big-O complexity estimates, complete with syntax highlighting and optional AI-powered code reviews.

## 🎯 What It Does

Understanding time complexity (Big-O notation) is crucial for writing efficient algorithms, identifying bottlenecks, making informed optimization decisions, and passing technical interviews.

Analyzing complexity manually is tedious and error-prone. This tool **automates** the entire process—detecting loops, recursion, and functions, then annotating code with Big-O estimates and explanations.

### Core Features

- 📊 **Automatic Detection** - Identifies loops, recursion, and functions across 13+ programming languages
- 🧮 **Complexity Estimation** - Calculates Big-O complexity (O(1), O(n), O(n²), O(log n), etc.)
- 💬 **Inline Annotations** - Inserts explanatory comments directly into your code
- 🎨 **Syntax Highlighting** - Generates beautiful HTML previews with orange-colored complexity comments
- 🤖 **AI Code Review** - Optional LLaMA-powered analysis for optimization suggestions
- 💾 **Export Options** - Download annotated source code and Markdown previews

## 🌐 Supported Languages

Python • JavaScript • TypeScript • Java • C • C++ • C# • Go • PHP • Swift • Ruby • Kotlin • Rust

## 🛠️ Tech Stack

- **HuggingFace Transformers** - LLM model loading and inference
- **LLaMA 3.2** - AI-powered code review
- **Gradio** - Interactive web interface
- **Pygments** - Syntax highlighting
- **PyTorch** - Deep learning framework
- **Regex Analysis** - Heuristic complexity detection

## 📋 Prerequisites

- Python 3.12+
- `uv` package manager (or `pip`)
- 4GB+ RAM (for basic use without AI)
- 14GB+ RAM (for AI code review with LLaMA models)
- Optional: NVIDIA GPU with CUDA (for model quantization)

## 🚀 Installation

### 1. Clone the Repository

```bash
cd week4
```

### 2. Install Dependencies

```bash
uv pip install -U pip
uv pip install transformers accelerate gradio torch --extra-index-url https://download.pytorch.org/whl/cpu
uv pip install bitsandbytes pygments python-dotenv
```

> **Note:** This installs the CPU-only version of PyTorch. For GPU support, remove the `--extra-index-url` flag.

### 3. Set Up HuggingFace Token (Optional - for AI Features)

Create a `.env` file in the `week4` directory:

```env
HF_TOKEN=hf_your_token_here
```

Get your token at: https://huggingface.co/settings/tokens

> **Required for:** LLaMA models (requires accepting Meta's license agreement)

## 💡 Usage

### Option 1: Jupyter Notebook

Open and run `week4 EXERCISE_hopeogbons.ipynb`:

```bash
jupyter notebook "week4 EXERCISE_hopeogbons.ipynb"
```

Run all cells in order. The Gradio interface will launch at `http://127.0.0.1:7861`

### Option 2: Web Interface

Once the Gradio app is running:

#### **Without AI Review (No Model Needed)**

1. Upload a code file (.py, .js, .java, etc.)
2. Uncheck "Generate AI Code Review"
3. Click "🚀 Process & Annotate"
4. View syntax-highlighted code with Big-O annotations
5. Download the annotated source + Markdown

#### **With AI Review (Requires Model)**

1. Click "🔄 Load Model" (wait 2-5 minutes for first download)
2. Upload your code file
3. Check "Generate AI Code Review"
4. Adjust temperature/tokens if needed
5. Click "🚀 Process & Annotate"
6. Read AI-generated optimization suggestions

## 📊 How It Works

### Complexity Detection Algorithm

The tool uses **heuristic pattern matching** to estimate Big-O complexity:

1. **Detect Blocks** - Regex patterns find functions, loops, and recursion
2. **Analyze Loops** - Count nesting depth:
   - 1 loop = O(n)
   - 2 nested loops = O(n²)
   - 3 nested loops = O(n³)
3. **Analyze Recursion** - Pattern detection:
   - Divide-and-conquer (binary search) = O(log n)
   - Single recursive call = O(n)
   - Multiple recursive calls = O(2^n)
4. **Aggregate** - Functions inherit worst-case complexity of inner operations

### Example Output

**Input (Python):**

```python
def bubble_sort(arr):
    for i in range(len(arr)):
        for j in range(len(arr) - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
```

**Output (Annotated):**

```python
def bubble_sort(arr):
# Big-O: O(n^2)
# Explanation: Nested loops indicate quadratic time.
    for i in range(len(arr)):
        for j in range(len(arr) - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
```

## 🧠 AI Model Options

### CPU/Mac (No GPU)

- `meta-llama/Llama-3.2-1B` (Default, ~1GB, requires HF approval)
- `gpt2` (No approval needed, ~500MB)
- `microsoft/DialoGPT-medium` (~1GB)

### GPU Users

- Any model with 8-bit or 4-bit quantization enabled
- `meta-llama/Llama-2-7b-chat-hf` (requires approval)

### Memory Requirements

- **Without quantization:** ~14GB RAM (7B models) or ~26GB (13B models)
- **With 8-bit quantization:** ~50% reduction (GPU required)
- **With 4-bit quantization:** ~75% reduction (GPU required)

## ⚙️ Configuration

### File Limits

- Max file size: **2 MB**
- Supported extensions: `.py`, `.js`, `.ts`, `.java`, `.c`, `.cpp`, `.cs`, `.go`, `.php`, `.swift`, `.rb`, `.kt`, `.rs`

### Model Parameters

- **Temperature** (0.0 - 1.5): Controls randomness
  - Lower = more deterministic
  - Higher = more creative
- **Max Tokens** (16 - 1024): Maximum length of AI review

## 📁 Project Structure

```
week4/
├── week4 EXERCISE_hopeogbons.ipynb  # Main application notebook
├── README.md                         # This file
└── .env                             # HuggingFace token (create this)
```

## 🐛 Troubleshooting

### Model Loading Issues

**Error:** "Model not found" or "Access denied"

- **Solution:** Accept Meta's license at https://huggingface.co/meta-llama/Llama-3.2-1B
- Ensure your `.env` file contains a valid HF_TOKEN

### Memory Issues

**Error:** "Out of memory" during model loading

- **Solution:** Use a smaller model like `gpt2` or `microsoft/DialoGPT-medium`
- Try 8-bit or 4-bit quantization (GPU required)

### Quantization Requires GPU

**Error:** "Quantization requires CUDA"

- **Solution:** Disable both 4-bit and 8-bit quantization checkboxes
- Run on CPU with smaller models

### File Upload Issues

**Error:** "Unsupported file extension"

- **Solution:** Ensure your file has one of the supported extensions
- Check that the file size is under 2MB

## 🎓 Use Cases

- **Code Review** - Automated complexity analysis for pull requests
- **Interview Prep** - Understand algorithm efficiency before coding interviews
- **Performance Optimization** - Identify bottlenecks in existing code
- **Education** - Learn Big-O notation through practical examples
- **Documentation** - Auto-generate complexity documentation

## 📝 Notes

- First model load downloads weights (~1-14GB depending on model)
- Subsequent runs load from cache (much faster)
- Complexity estimates are heuristic-based, not formally verified
- For production use, consider manual verification of critical algorithms

## 🤝 Contributing

This is a learning project from the Andela LLM Engineering course (Week 4). Feel free to extend it with:

- Additional language support
- More sophisticated complexity detection
- Integration with CI/CD pipelines
- Support for space complexity analysis

## 📄 License

Educational project - use as reference for learning purposes.

## 🙏 Acknowledgments

- **OpenAI Whisper** for inspiration on model integration
- **HuggingFace** for providing the Transformers library
- **Meta** for LLaMA models
- **Gradio** for the excellent UI framework
- **Andela** for the LLM Engineering curriculum

---

**Built with ❤️ as part of Week 4 LLM Engineering coursework**
