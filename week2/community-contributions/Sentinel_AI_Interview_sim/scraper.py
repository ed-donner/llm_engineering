"""
scraper.py — Domain-Based Interview Question Scraper

Scrapes AI or ML interview questions from URLs stored in .env.
Triggered as a tool call when the candidate picks a domain.
Follows the same pattern as the reference scraper.py.
"""

import os
import json
from bs4 import BeautifulSoup
import requests

# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

# Maps domain choice to the .env variable name
DOMAIN_URL_MAP = {
    "AI": "AI_QUESTIONS_URL",
    "ML": "ML_QUESTIONS_URL",
}


def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url;
    truncate to 5,000 characters as a sensible limit for interview questions.
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:5_000]


def _parse_questions(raw_text):
    """Extract question-like lines from raw scraped text."""
    lines = raw_text.split("\n")
    questions = []
    for line in lines:
        line = line.strip()
        # Look for lines that look like questions (end with ? or start with a number)
        if not line:
            continue
        if line.endswith("?") or (len(line) > 20 and any(line.startswith(f"{i}") for i in range(1, 100))):
            # Clean up numbering
            cleaned = line.lstrip("0123456789.)- ").strip()
            if len(cleaned) > 15:  # Skip very short lines
                questions.append(cleaned)

    return questions[:20]  # Return top 20 questions


def scrape_domain_questions(domain):
    """
    Scrape interview questions for the chosen domain (AI or ML).
    URLs are read from .env file.
    
    Args:
        domain: "AI" or "ML"
    
    Returns:
        JSON string with list of questions, or error message.
    """
    domain_upper = domain.upper().strip()
    env_key = DOMAIN_URL_MAP.get(domain_upper)

    if not env_key:
        return json.dumps({"error": f"Invalid domain '{domain}'. Choose 'AI' or 'ML'."})

    url = os.getenv(env_key)
    if not url:
        return json.dumps({"error": f"No URL configured for {domain}. Set {env_key} in .env."})

    print(f"SCRAPER TOOL CALLED: Fetching {domain_upper} questions from {url}", flush=True)

    try:
        contents = fetch_website_contents(url)
        questions = _parse_questions(contents)

        if not questions:
            # Fallback to default questions if parsing fails
            questions = _get_fallback_questions(domain_upper)
            print(f"  → Using fallback questions ({len(questions)} questions)")
        else:
            print(f"  → Scraped {len(questions)} questions successfully")

        return json.dumps({
            "domain": domain_upper,
            "source": url,
            "questions": questions,
            "count": len(questions)
        })

    except Exception as e:
        print(f"  → Scraping failed: {e}")
        questions = _get_fallback_questions(domain_upper)
        return json.dumps({
            "domain": domain_upper,
            "source": "fallback",
            "questions": questions,
            "count": len(questions),
            "note": f"Scraping failed ({e}), using fallback questions."
        })


def _get_fallback_questions(domain):
    """Return hardcoded fallback questions if scraping fails."""
    fallback = {
        "AI": [
            "What is the difference between Artificial Intelligence and Machine Learning?",
            "Explain the concept of a neural network and how it learns.",
            "What are the different types of AI: narrow, general, and super AI?",
            "What is natural language processing and what are its main challenges?",
            "Explain the Turing Test and its significance in AI.",
            "What is reinforcement learning? Give a real-world example.",
            "What are Generative Adversarial Networks (GANs) and how do they work?",
            "Explain the concept of transfer learning and when you would use it.",
            "What is the difference between supervised and unsupervised learning?",
            "What are transformer models and why are they important in modern AI?",
        ],
        "ML": [
            "What is the bias-variance tradeoff in machine learning?",
            "Explain the difference between classification and regression.",
            "What is overfitting and how can you prevent it?",
            "Describe the working of a Random Forest algorithm.",
            "What is gradient descent and how does it work?",
            "Explain cross-validation and why it is used.",
            "What is the difference between L1 and L2 regularization?",
            "How does a Support Vector Machine (SVM) work?",
            "What are precision, recall, and F1-score?",
            "Explain the concept of dimensionality reduction and name two techniques.",
        ],
    }
    return fallback.get(domain, fallback["AI"])
