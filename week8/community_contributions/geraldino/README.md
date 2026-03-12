# Smart Deal Digest. AI-Powered Deal Hunter

I am excited to desgin an autonomous multi-agent pipeline that monitors e-commerce deals around the clock, estimates real market value using a fine-tuned LLM, and emails you only the genuine bargains.

---

## How the system works

Three agents collaborate in a continuous pipeline:

**1. ScannerAgent** fetches live deals from e-commerce RSS feeds and sends them to GPT-4o-mini, which selects the 5 most promising products with verified, clearly-stated prices.

**2. PricerAgent** sends each deal to a fine-tuned Qwen2.5-3B model trained on 20,000 product pricing examples using QLoRA to estimate real market value. The model is deployed on Modal as a persistent cloud service, so inference takes seconds rather than minutes.

**3. MessagingAgent** sends a Gmail email digest whenever the listed price is meaningfully below the estimated value (default threshold: $20).

The pipeline runs on a 90-second timer inside a live Gradio UI. Click any deal row to send yourself an individual alert email.

---

## Project Highlights

- Fine-tuned Qwen2.5-3B with LoRA adapters on 20,000 product price examples
- Model hosted on HuggingFace, served via Modal T4 GPU
- Memory persistence via `memory.json`
- Single model architecture — no vector database or ensemble needed

---

## File Structure

```
geraldino/
├── main.py              # Gradio UI + DealDigestFramework orchestrator
├── pricer_modal.py      # Modal cloud deployment for the pricing model
├── README.md
└── agent/
    ├── __init__.py
    └── agents.py        # All agents: ScrapedDeal, ScannerAgent, PricerAgent, MessagingAgent
```

---

## Setup

### 1. Clone and navigate

```bash
cd geraldino
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install gradio openai feedparser beautifulsoup4 requests \
            transformers peft bitsandbytes accelerate \
            pydantic tqdm python-dotenv torch modal
```

### 4. Configure your .env file

Create a `.env` file in the `geraldino/` folder:

```env
OPENAI_API_KEY=sk-...

SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your_16_char_app_password
EMAIL_FROM=your.email@gmail.com
EMAIL_TO=your.email@gmail.com
```

> **Gmail App Password:** Go to myaccount.google.com/apppasswords, create a new app password, and paste the 16-character code (no spaces) as `SMTP_PASSWORD`. Do NOT use your real Gmail password.

---

## Deploy the Pricing Model to Modal

The PricerAgent calls a fine-tuned Qwen2.5-3B model hosted on Modal. You need to deploy it once before running the app.

### 1. Install and authenticate Modal

```bash
pip install modal
modal setup
```

### 2. Add your HuggingFace token as a Modal secret

```bash
modal secret create huggingface-secret HF_TOKEN=hf_your_token_here
```

Get your token from: huggingface.co → Settings → Access Tokens

### 3. Deploy the model

```bash
modal deploy pricer_modal.py
```

### 4. Test it works

```bash
modal run pricer_modal.py
# Expected output: Test estimate: $XXX.00
```

---

## Run

```bash
python main.py
```

Open your browser at **[http://127.0.0.1:7860](http://127.0.0.1:7860)**

The pipeline runs immediately on startup, then every 90 seconds automatically. When opportunities are found, a digest email is sent and the table updates. Click any row to send yourself an individual deal alert.

---

## Using Your Own Model

The pricing model is hardcoded in `pricer_modal.py`. To swap in your own fine-tuned model, replace these three lines:

```python
BASE_MODEL    = "Qwen/Qwen2.5-3B"                            # base model used during training
HF_MODEL_REPO = "Geraldino07/price-2026-03-09_21.46.47"      # your HuggingFace repo
HF_REVISION   = "285f0bdd4a8f6f30d6f6af59976e69ecc7d4688c"   # your best checkpoint commit hash
```

Then redeploy: `modal deploy pricer_modal.py`

---

## Architecture Comparison

This project deliberately explores a simpler architecture than Ed's reference implementation:


| Feature          | Ed's Version               | This Project            |
| ---------------- | -------------------------- | ----------------------- |
| Model            | LLaMA 3.2-3B (Modal)       | Qwen2.5-3B (Modal)      |
| Pricing strategy | EnsembleAgent + RAG        | Single fine-tuned model |
| Vector database  | ChromaDB (200k embeddings) | None                    |
| Notifications    | Pushover push              | Gmail email             |
| Agents           | 7                          | 3                       |


The central question this project explores: *can a single well-trained smaller model deliver useful deal intelligence without vector database infrastructure?* Based on results, the answer is yes — with good training data, it can.

---

## Requirements

- Python 3.11+
- OpenAI API key
- Gmail account with App Password enabled
- Modal account (free tier is sufficient)
- HuggingFace account with a fine-tuned pricing model

