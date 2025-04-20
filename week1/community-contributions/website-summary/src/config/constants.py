#!/usr/bin/env python
# coding: utf-8

"""
Constants for the Website Summary Tool
"""

# OpenAI Configuration
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEST_MESSAGE = "Hello, GPT! This is my first ever message to you! Hi!"

# Web Scraping Configuration
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

# # Default prompts
# DEFAULT_TEST_SYSTEM_PROMPT = ("You are an assistant that analyzes the contents of a website "
#                 "and provides a short summary, ignoring text that might be navigation related. "
#                 "Respond in markdown.")

# DEFAULT_TEST_USER_PROMPT_TEMPLATE = """
# You are looking at a website titled {title}
# The contents of this website is as follows; 
# please provide a short summary of this website in markdown.
# If it includes news or announcements, then summarize these too.

# {text}
# """