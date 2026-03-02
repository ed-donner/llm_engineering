"""
# News Vibe Checker

A simple Python tool to check the general sentiment or "vibe" of recent Hacker News stories about any topic using an LLM.

## Features

- **Fetches Top 5 Hacker News Stories:** Uses the Algolia API to search for stories about any given topic.
- **LLM-Powered Sentiment Analysis:** Aggregates titles and sends them to an LLM for vibe/sentiment evaluation (optimistic, skeptical, or fearful).
- **Easy to Use:** Just set your API key and run to analyze any topic.

## How It Works

1. **Enter a topic** you'd like to analyze.
2. The script **fetches the latest 5 Hacker News stories** on that topic.
3. It **passes the story titles to an LLM**, which returns a one-sentence summary of the general sentiment.

## Setup Instructions

1. **Clone this repository** and open `news_vibe_checker.ipynb` in Jupyter or view the script.
2. **Set your API key** for OpenRouter or compatible OpenAI endpoint.
3. **Install dependencies:**
   ```
   pip install openai requests
   ```
4. **Run the script** (or each cell, if in a notebook).

## Example Output

```
--- Checking the vibe for: AI regulation ---
Extracted Titles:
- [list of HN story titles...]

--- ANALYSIS ---
The general sentiment is optimistic because the stories focus on positive advancements and constructive approaches to AI regulation.
```

## Customization

- You can modify the LLM prompt or change the number of stories in the `get_hn_vibe` function.

## Requirements

- Python 3.7+
- OpenAI-compatible API key (from OpenRouter, OpenAI, etc.)
- `openai`, `requests`

## Troubleshooting

- Ensure your API key is valid and that the endpoint URL is correct.
- If the LLM or API URL returns a 404 or other error, check your environment variables and credentials.

## Credits

Created by [philmuhire]

"""