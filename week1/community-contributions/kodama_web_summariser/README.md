# 🚪 木霊 (Kodama) — Streaming Web Summarizer & Ingestion Portal

Kodama is an ultra-fast, visually stunning intelligence tool that extracts content from modern web pages, bypasses context-window limitations using a custom Map-Reduce chunking pipeline, and generates personalized, real-time summaries. 

Powered by the **Groq API (Llama 3.3 70B)** and wrapped in a bespoke, Glassmorphism-inspired Streamlit interface, this application proves that data-heavy Python dashboards can be both lightning-fast and beautifully designed.

---

## ✨ Core Engineering Features

### 1. Lightning-Fast Cloud Inference (Streaming Tokens)
Traditional LLM wrappers suffer from high Time-To-First-Token (TTFT) latency, freezing the UI while waiting for massive text payload computations. Kodama utilizes the Groq Cloud SDK with `"stream": True`, hooking directly into Streamlit's native generator protocol to stream the response onto the viewport in milliseconds.

### 2. Map-Reduce Semantic Slicer (Context Window Management)
Feeding entire Wikipedia articles or dense documentation into an LLM often causes memory saturation or context degradation. Kodama implements a **Map-Reduce processing pipeline**:
* **Map Phase:** The ingestion engine slices raw HTML text at natural paragraph boundaries (`\n`) into semantic chunks capped at 4,000 characters. Each chunk is processed individually to extract core assertions.
* **Reduce Phase:** The compiled intermediate summaries are fed back into a final synthesis prompt, guaranteeing zero token-limit crashes regardless of the target webpage's length.

### 3. Dynamic DOM Parsing & Media Extraction
Utilizing `BeautifulSoup4`, the app strips out modern web noise (scripts, headers, navbars) to isolate the core semantic `<p>` tags. Concurrently, it scans the document's `<meta>` properties (specifically OpenGraph `og:image` and Twitter cards) to dynamically pull and display the webpage's primary featured image.

### 4. Secure Environment Authentication
API keys are handled completely locally via `python-dotenv`. The application automatically detects and loads the `.env` configuration on boot, preventing accidental token leakage to public version control while maintaining a fallback manual-entry UI if the environment file is missing.

---

## 🛠️ Technical Stack

* **Frontend Dashboard:** Streamlit (Custom Glassmorphism CSS Layer, Responsive Column Grid)
* **DOM Scraping & Parsing:** Python 3.13+, BeautifulSoup4, Requests, urllib
* **Inference Engine:** Groq Cloud API (`llama-3.3-70b-versatile`)
* **Environment Security:** Python-dotenv

---

## 🏁 Getting Started

### 1. Prerequisites
Ensure you have Python 3.8+ installed and a free API key from the [Groq Console](https://console.groq.com/).