# Day 5: Company Expert System / Data Bank

Instead of a brochure, this project builds an **expert system** that answers questions about a company based on information aggregated from its website. Users can ask questions and receive informed, accurate answers—or a clear "I don't know" when the information isn't available.

---

## Overview

1. **Extract** all links from the company's website
2. **Select** relevant links for the data bank (broader than a brochure)
3. **Build** a knowledge base from the landing page + selected pages
4. **Answer** user questions via an LLM with strict guardrails
5. **Cache** answers to avoid redundant API calls

---

## Step 0: Extract Links

Uses `fetch_website_links(url)` from `scraper.py` to extract all links from the website.

---

## Step 1: Select Relevant Links for the Data Bank

Uses `select_relevant_links()` to filter links via an LLM. For a **data bank** (vs. brochure), we want a broader set of links—anything that could inform answers.

**Link system prompt:**

```
You are provided with a list of links found on a webpage.
For a **data bank** (vs. a brochure), we want a **broader** set of links — anything that could inform answers:
- About, Company, Team
- Products, Services, Solutions
- Blog, News, Articles
- Careers, Jobs, Culture
- Contact, Support, FAQ, Help
- Documentation, Docs, Guides

**Exclude:** Terms of Service, Privacy Policy, cookie banners, social media, email `mailto:` links.

Respond in JSON only:
{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}
```

**Link user prompt template** (placeholders: `{url}`, `{links}`):

```
Here are the links found on {url}. Select those relevant for a company knowledge base.
Return full absolute URLs in JSON format. Do not include Terms of Service, Privacy, or email links.

Links:
{links}
```

---

## Step 2: Fetch Content and Build the Knowledge Base

Uses `build_knowledge_base()` to:

- Fetch the landing page content
- Fetch content from each selected link
- Assemble into a structured string (truncated to ~10k chars for context limits)

Structure: `## Landing Page` + `## Relevant Links` with `### Link: [type]` sections for each page.

---

## Step 3: Expert System Prompts

The expert system uses strict system and user prompts so the model answers only from the knowledge base and clearly states when it lacks information.

**System prompt template** (placeholder: `{company_name}`):

```
You are an expert system for {company_name}. Your ONLY source of information is the knowledge base provided below. Answer questions accurately based on it. You must NOT use external knowledge or assumptions.

RULES:
1. Answer questions ONLY based on the provided knowledge base.
2. If the knowledge base does not contain enough information to answer, say: "I don't have enough information in the provided content to answer this question."
3. If the question is unrelated to the company (e.g., general trivia, other companies), say: "This question appears unrelated to {company_name}. I can only answer questions about the information in the knowledge base."
4. When you do have an answer, cite the relevant section or page when helpful (e.g., "According to the About page...").
5. Be concise but accurate. Do not speculate or hallucinate.

OUTPUT FORMAT:
- Do NOT repeat the user's question.
- Start with your answer. If you cite sources, end with a "References:" section listing relevant URLs from the knowledge base.
- Use markdown. Do NOT wrap your response in code blocks.

Example (when you have an answer):
**Answer:** The main product is the Hugging Face Hub and API, which provides access to models, datasets, and ML tools.

**References:**
- https://huggingface.co/about

Example (when you lack information):
I don't have enough information in the provided content to answer this question.
```

**User prompt template** (placeholders: `{company_name}`, `{url}`, `{knowledge_base}`, `{question}`):

```
Knowledge base for {company_name} (from {url}):

---
{knowledge_base}
---

Question: {question}
```

---

## Step 4: Streaming

`_stream_response(stream)` streams the model output to the display and returns the full accumulated text for caching.

---

## Step 5: ExpertSystem Class

The `ExpertSystem` class encapsulates the full flow:

| Method | Description |
| --- | --- |
| `__init__(url, company_name)` | Fetches links, selects relevant ones, builds knowledge base |
| `answer_question(question, use_cache=True)` | Answers a question; checks cache first if `use_cache=True` |
| `clear_cache()` | Clears the question-answer cache |

**Prompt handling:**

- Prompts are defined as module-level templates with `{placeholder}` syntax
- `_build_prompt(template, **kwargs)` formats templates via `str.format()`
- Keeps prompts separate from logic for easier maintenance

**Cache:**

- `_cache`: dict mapping normalized question → answer
- `_normalize_question(question)`: strips, lowercases, and collapses whitespace for cache keys (so "What is X?" and "what is x?" hit the same cache entry)
- Repeated questions are served from cache without an API call

---

## Usage

```python
# Initialize (fetches links, builds knowledge base)
expert_system = ExpertSystem(url="https://huggingface.co", company_name="Hugging Face")

# First call — hits the API
expert_system.answer_question("What is the main product of Hugging Face?")

# Same question again — served from cache (no API call)
expert_system.answer_question("What is the main product of Hugging Face?")

# Different question
expert_system.answer_question("Does Hugging Face have a careers page?")

# Bypass cache
expert_system.answer_question("...", use_cache=False)

# Clear cache
expert_system.clear_cache()
```

---

## Dependencies

- `scraper.py`: `fetch_website_links`, `fetch_website_contents`
- OpenAI client (via OpenRouter)
- `gpt-4o-mini` for link selection, `gpt-5-nano` for Q&A
