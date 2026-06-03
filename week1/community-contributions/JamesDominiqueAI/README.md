# 📄 Document Summarization Pipeline

A hierarchical document summarization system using:

- Cloud model: `gpt-4o-mini`
- Local fallback: `llama3.2:3b` via Ollama
- Multi-format document ingestion
- Recursive summarization (chunk → batch → executive summary)
- Automatic dynamic output naming

---

## 🚀 Features

- Supports `.txt`, `.pdf`, `.docx`
- Smart sentence-aware chunking
- Cloud-first architecture with automatic local fallback
- Executive-level structured summary output
- Automatic output filename generation
- Timestamp versioning to prevent overwrite
- Structured logging

---

## 🏗 Architecture Overview

```
Document → Text Extraction → Chunking → 
Chunk Summaries → Batch Reduction → 
Final Executive Summary → DOCX Export
```

### Execution Strategy

1. Attempt summarization using OpenAI (cloud)
2. If unavailable → fallback to Ollama (local model)
3. If both fail → raise runtime error

---

## 📦 Requirements

### Python Version
Python 3.9+

### Dependencies

Install via:

```bash
pip install openai python-docx PyPDF2 docx2txt
```

If using local fallback:

```bash
ollama pull llama3.2:3b
```

Ollama must be running locally:

```bash
ollama serve
```

---

## 🔑 Environment Configuration

Set your OpenAI API key (for cloud mode):

### Windows (PowerShell)

```powershell
setx OPENAI_API_KEY "your_key_here"
```

### macOS / Linux

```bash
export OPENAI_API_KEY="your_key_here"
```

If no key is found, the system automatically switches to local mode.

---

## ▶️ Usage

Edit inside `main`:

```python
input_file = r"path_to_your_file.docx"
```

Run:

```bash
python summarizer.py
```

Output will be saved automatically as:

```
<original_filename>_summary_<timestamp>.docx
```

Example:

```
report.docx
→ report_summary_20260226_014501.docx
```

---

## 📂 Supported Input Formats

| Format | Supported | Notes |
|--------|----------|-------|
| .txt   | ✅ | UTF-8 only |
| .pdf   | ✅ | Text-based PDFs only |
| .docx  | ✅ | Extracted via docx2txt |
| .doc   | ❌ | Not supported |
| Scanned PDF | ❌ | No OCR support |

---

# ⚠️ Program Limitations

## 1️⃣ No OCR Support
- Image-based PDFs are not supported.
- Only text-based PDFs work.
- No OCR integration (e.g., Tesseract).

---

## 2️⃣ Token / Context Limits
- Chunking is character-based, not token-aware.
- Very large documents may:
  - Increase runtime
  - Increase API cost (cloud mode)
  - Reduce coherence across chunks

---

## 3️⃣ Sequential Processing
- Chunk summarization runs sequentially.
- No multiprocessing or async implementation.
- Large documents will take longer.

---

## 4️⃣ No Cost Control
- No token usage tracking.
- No spending cap.
- Large documents may generate unexpected API costs.

---

## 5️⃣ Model Dependency

Cloud Mode:
- Requires valid OpenAI API key.
- Depends on model availability.

Local Mode:
- Requires Ollama installed.
- Requires `llama3.2:3b` downloaded.
- Requires local server running.

If Ollama is not running, fallback fails.

---

## 6️⃣ Basic Sentence Splitting
Chunk splitting uses:

```python
text.rfind(".", 0, chunk_size)
```

Limitations:
- Not language-aware.
- May split incorrectly on abbreviations.
- Not NLP-optimized.

---

## 7️⃣ No Structured Output Validation
- No JSON schema enforcement.
- No format validation.
- Model output saved as-is.

---

## 8️⃣ Hardcoded Paths
- Input and output paths are defined in code.
- No CLI argument support.
- No configuration file support.

---

## 9️⃣ No Retry / Backoff Strategy
- If a request fails:
  - Switches model
  - No exponential retry logic
- Network instability may cause full failure.

---

## 🔒 Security Considerations
- Cloud mode sends documents to OpenAI API.
- Sensitive documents should use local mode only.
- No encryption-at-rest mechanism implemented.

---

## 📈 Performance Expectations

| Document Size | Expected Behavior |
|--------------|------------------|
| < 20 pages | Fast |
| 20–100 pages | Moderate |
| 100+ pages | Slower |
| 300+ pages | High runtime |

Local 3B model will be slower than cloud.

---

## 🛠 Suggested Future Improvements

- Token-aware chunking
- Async parallel processing
- CLI support with argparse
- JSON schema enforcement
- Cost tracking
- OCR integration
- Docker containerization
- REST API wrapper
- Caching mechanism
- Progress bar
- Streaming summarization

---

## 📊 Design Pattern

Recursive Map-Reduce LLM Summarization  
With Resilient Dual-Execution (Cloud + Local Fallback)

Suitable for:
- Executive briefings
- Policy analysis
- Strategic planning documents
- Research synthesis

---