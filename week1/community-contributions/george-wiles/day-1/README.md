# GitHub README Summarizer (LLM Engineering Project)
## Day 1 use model="gpt-4.1-mini"

Ever wondered what happens when you let an LLM summarize an llm_engineering git repository README using system and user prompts? 

## Example

*input*: https://github.com/ed-donner/llm_engineering

*system_prompt* = You are a philosophical new age software engineer that analyzes the contents of GitHub repositories, and provides a critical thinking, open-minded and humorous summary.
Respond in markdown. Do not wrap the markdown in a code block - respond just with the markdown.

*user_prompt_prefix* = Here are the contents of a GitHub repository README.
Provide a short summary of this repository in the context of the system prompt.

*Response*: 
Journey Into the Mystical Realm of LLM Engineering
Welcome, fellow cosmic coder! This repository is more than just a collection of files — it’s your eight-week transcendental voyage to mastering Large Language Models (LLMs) and AI at large. Guided by Edward Donner, you’re invited not just to learn, but to become the AI whisperer, embracing the art of prompt crafting, model tuning, and building agentic AI projects that dazzle and inspire.

## Use Case

As a developer, I would like to search GitHub repositories for a category [..., 'LLM Engineering'] 
and use LLM to return a summarization of the README files of projects that most closely match my search category using the user and system prompts
outlined in day1.ipynb.


## How It Works
1. User provides a GitHub repository URL (examples in `repos.txt`), one or two at a time. :-)
2. The notebook automatically fetches the `README.md` via raw GitHub URLs.
3. The retrieved README text is sent to an LLM for summarization, give the system and user prompts
4. The generated summary is displayed — .

## Files
- `summarizer.ipynb` – Main Jupyter Notebook implementation.
- `repos.txt` – A list of GitHub repositories related to LLM engineering.
- `README.md` – This documentation file.

## Requirements
- Python 3.9+
- `requests`
- Access to OpenAI / compatible LLM API

