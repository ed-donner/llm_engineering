# paperSuMMARiZER

A local AI-powered research paper summarizer. Paste any research paper URL and get a clean, structured markdown summary — including title, authors, methodology, technologies, references, and the research gap — all running locally via Ollama.

---

## How It Works

1. A research paper URL is passed to [Jina AI Reader](https://jina.ai/reader/) which scrapes the full page content.
2. The content is sent to a local `llama3.2:3b` model running via Ollama.
3. The model extracts and formats the key sections into clean markdown.

---

## Installation Guide

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running locally
- A [Jina AI](https://jina.ai) API key (free tier available)

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/your-username/llm_engineering.git
cd llm_engineering
```

### Step 2 — Create and Activate a Virtual Environment

```bash
python -m venv .venv
```

**Windows:**

```bash
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

Or if you use conda:

```bash
conda env create -f environment.yml
conda activate llm_engineering
```

### Step 4 — Pull the Model with Ollama

Make sure Ollama is running, then pull the required model:

```bash
ollama pull llama3.2:3b
```

### Step 5 — Configure Your API Key

Create a `.env` file in the project root:

```
JINA_API_KEY=your_jina_api_key_here
```

> **Note:** The Jina AI Reader API key is used to scrape research paper pages. You can get a free key at [https://jina.ai](https://jina.ai).

### Step 6 — Run the Notebook

Open `AI@Karam's/paperSuMMARiZER/paperSUMMARiZER.ipynb` in VS Code or JupyterLab and run all cells.

---

## Usage

Set your target paper URL in the notebook:

```python
paper_url = 'https://your-research-paper-url-here'
```

Then run the final cell:

```python
display_summary(paper_url)
```

---

## Output Example

Below is a sample output generated for an AI retinal health assessment paper:

---

**Title**

AI-Powered, Automated, and Portable Device for Retinal Health Assessment: A Review and Future Directions

---

**Abstract**

The advent of AI-powered technologies has revolutionized various fields of science and medicine. In this review article, we explore the development, applications, and future directions of an AI-powered, automated, and portable device designed to assess retinal health.

---

**Methods**

A systematic review of existing literature was conducted, including peer-reviewed articles, conference proceedings, and patents. Key characteristics, applications, benefits, limitations, and future directions of AI-powered retinal devices were analysed.

---

**Discussion**

The analysis revealed several AI-powered devices capable of detecting various retinal diseases with high accuracy, leveraging computer vision algorithms, deep learning techniques, and machine learning models.

---

**Key Results Table**

| Criteria           | Device A          | Device B          | Device C          |
| ------------------ | ----------------- | ----------------- | ----------------- |
| Detection accuracy | 95% (sensitivity) | 90% (specificity) | 98.5% (precision) |
| Portability        | Yes               | No                | Yes               |
| Affordability      | ~$500             | ~$20,000          | ~$2,000           |

---

**Clinical Trial Results**

| Trial ID | Study Design    | Patients | Outcome            |
| -------- | --------------- | -------- | ------------------ |
| ITG001   | Case-control    | 100      | Sensitivity: 95.2% |
| ABT012   | Cross-sectional | 200      | Precision: 93.7%   |

---

**Conclusion**

The development of AI-powered, automated, and portable devices for retinal health assessment holds significant promise for improving global healthcare outcomes. Future directions should focus on standardising evaluation protocols and clinical trial methodologies.

---

## Tech Stack

| Component    | Tool                       |
| ------------ | -------------------------- |
| LLM          | `llama3.2:3b` via Ollama   |
| Web Scraping | Jina AI Reader API         |
| Notebook     | Jupyter / VS Code          |
| Display      | `IPython.display.Markdown` |

---

## License

MIT
