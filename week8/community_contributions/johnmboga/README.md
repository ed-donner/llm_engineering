# ⚡ Job Fit Agent

An agentic AI system that continuously monitors job board RSS feeds, scores each listing against your CV using a HuggingFace embedding model, and sends a Pushover notification whenever a strong match is found.

---

## Architecture

```
RSS Feeds (every N minutes)
      ↓
[Agent 1] Fetcher & Parser       — feedparser, deduplication cache
      ↓
[Agent 2] Embedding Fit Scorer   — HuggingFace all-MiniLM-L6-v2 (open source)
      ↓ (only jobs above threshold)
[Agent 3] Match Summariser       — Frontier LLM via OpenRouter (mistral-7b)
      ↓
[Agent 4] Pushover Notifier      — Push notification to your phone
      ↓
[Orchestrator] coordinates loop, state, and Gradio UI updates
```

---

## Run the app

```bash
python app.py
```

Open the gradio app with the given url in your browser.

---

## How to Use

1. Enter your name (appears in Pushover notifications)
2. Paste your CV or a profile summary in the text area
3. Optionally add job preferences (role type, location, tech stack)
4. Set your fit score threshold (60% recommended to start)
5. Set the check interval (5 minutes recommended)
6. Add or modify RSS feed URLs
7. Click **START MONITORING**

The agent will run in the background. When a matching job is found:

- It appears in the **Matches** tab in the UI
- A Pushover notification is sent to your phone with the match summary and a direct link to the job listing

---

## RSS Feeds

The following feeds are included by default:

| Feed             | URL                                        |
| ---------------- | ------------------------------------------ |
| RemoteOK         | https://remoteok.com/remote-jobs.rss       |
| We Work Remotely | https://weworkremotely.com/remote-jobs.rss |

--

## Models Used

| Agent      | Model                                          | Type                      | Why                                                  |
| ---------- | ---------------------------------------------- | ------------------------- | ---------------------------------------------------- |
| Fit Scorer | `sentence-transformers/all-MiniLM-L6-v2`       | Open Source (HuggingFace) | Fast, free, runs locally, strong semantic similarity |
| Summariser | `mistralai/mistral-7b-instruct` via OpenRouter | Frontier API              | Cheap, fast, good at structured text generation      |

---
