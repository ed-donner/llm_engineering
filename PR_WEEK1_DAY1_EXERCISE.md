# Pull Request: Week 1 Day 1 – Email subject-line exercise

Use this as the **description** when you open the PR on GitHub.

---

## Title

**Week 1 Day 1: Add email subject-line summarization exercise**

---

## Description

### What

This PR completes the first “try yourself” exercise in `week1/day1.ipynb`: a **summarization** prototype that suggests a short email subject line from the email body (as suggested in the notebook).

### Changes

- **`week1/day1.ipynb`**  
  - Replaced the placeholder in the “Before you continue – now try yourself” section with a working example:
    - `EMAIL_SYSTEM_PROMPT`: instructs the model to return only a short, clear subject line.
    - `suggest_subject(email_body)`: builds messages and calls the same OpenAI API pattern used elsewhere in the notebook (`gpt-4.1-mini`).
    - Example email body and `print("Suggested subject:", subject)` so the cell runs end-to-end.

### Why

- Aligns with the exercise text: apply summarization to a business use case and prototype it.
- Uses the same patterns as the rest of the lab (system + user messages, `openai.chat.completions.create`).
- Keeps the example minimal and easy to extend (e.g. different prompts or models).

### Checklist

- [x] Notebook runs (imports, API client, and exercise cell).
- [x] Only the intended exercise cell and its outputs are changed (other diff is from running the notebook).
- [ ] Changes are only in `community-contributions/` **or** you’ve agreed with the maintainer to change `week1/day1.ipynb`.

**Note:** [CONTRIBUTING.md](CONTRIBUTING.md) asks for changes only in `community-contributions/` unless agreed. If the maintainer prefers that, this same solution can be added under `week1/community-contributions/` (e.g. `day1-email-subject-exercise/`) and the PR can be updated to touch only that path.

---

## How to open the PR

1. Push your branch (if you haven’t already):
   ```bash
   git push origin week1-day1-email-subject-exercise
   ```

2. On GitHub, open your fork of `llm_engineering`, then:
   - Use “Compare & pull request” for the branch `week1-day1-email-subject-exercise`, or  
   - Go to **Pull requests → New pull request**, choose your branch, and set the base to `ed-donner/llm_engineering` `main`.

3. Set the **title** and **description** to the text above (or paste from this file).

4. Submit the pull request.
