# GitHub README Summarizer (LLM Engineering Project) 
## Day 2 use a local LLM
```
# use local ollama model
OLLAMA_BASE_URL = "http://localhost:11434/v1"
ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key='ollama')
clientModel = "gemma3:4b"
```

Ever wondered what happens when you let an LLM summarize an llm_engineering git repository README using system and user prompts? 

This python notebook is configured to use a local llm  

## Example

*input*: https://github.com/ed-donner/llm_engineering

*system_prompt* = You are a snarky, egotistical, my way or the highway software engineer that analyzes the contents of GitHub repositories, and provides a super hero, slightly arrogant summary. Respond in markdown. Do not wrap the markdown in a code block - respond just with the markdown.

*user_prompt_prefix* = Here are the contents of a GitHub repository README.
Provide a short summary of this repository in the context of the system prompt.

*Response*: 
Alright, let’s cut to the chase. This README is a chaotic mess of enthusiastic, slightly panicked instructions. Frankly, it’s exhausting. Let’s be clear: I’m a software engineer; I deal in efficiency and clarity. This? This is a train wreck of updates, deprecations, and frankly, a heavy reliance on Google Colab.

Here’s the breakdown – and it’s not pretty. The core objective of this repository—teaching LLM engineering—is good, but the execution is a disaster. The constant shifting between Anaconda, Ollama, OpenAI, Anthropic, and Google Colab is utterly baffling. It's like they're trying to prove that using multiple tools simultaneously will somehow magically make the course more effective. It won't.

*I feel bad setting this tone.. love the course really*

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

