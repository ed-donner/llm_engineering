## Email Digest Feature

To enable real email sending for the news agent demo, you must create a `.env` file in the project root with the following secrets:

```
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

By default, the agent will only print the email content for safety. To actually send emails, set `send_real_email=True` when calling `send_email_digest`. Your email provider may require an app password or special configuration for SMTP.
# Agentic AI News Scraper

Modular, production-ready agent for scraping, summarizing, and visualizing the latest AI news.

**Features:**
- Customizable news sources (RSS)
- LLM-powered semantic summarization (OpenAI)
- Automated word cloud visualization
- Email digest 
- Gradio web UI for interaction

**Quick Start:**
1. Install dependencies: `pip install -r requirements.txt`
2. Run: `python ai_news_agent.py` or launch the notebook for the UI

Edit sources and settings in the notebook or module as needed.
