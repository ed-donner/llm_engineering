# GitHub PR Assistant for the LLM Engineering Bootcamp

## Features

- **Models (via OpenRouter):**
  - GPT-4o-mini
  - GPT-4o
  - Claude 3.5 Sonnet
  - Gemini Flash 1.5
  - LLaMA 3.1 8B

- **Tools:**
  - `get_pr_guide` — Scrapes Ed Donner's official PR guide from [edwarddonner.com/pr](https://edwarddonner.com/pr)
  - `check_github_pr` — Uses the GitHub API to inspect a student's PR for issues such as:
    - Files outside `community-contributions`
    - File deletions
    - Too many files changed
    - And more

- **System Prompt:**
  - Acts as a Teaching Assistant that guides students through the 5-step PR submission process:
    1. Fork
    2. Branch
    3. Folder setup
    4. Commit
    5. Open PR

- **Chat Logic:**
  - Resolves all tool calls in a loop first, then streams the final answer back to the user.

- **Gradio UI:**
  - `ChatInterface` with a model selector dropdown, titled **"GitHub PR Assistant"**

---

**Status:**  
It's running — the output shows `OPENROUTER_API_KEY` looks good and the Gradio server launched on [http://127.0.0.1:7864](http://127.0.0.1:7864).
