# AI Immigration & Citizenship Guidance Assistant  

## ⚠️ Disclaimer

This project is **an educational example** showing how web scraping and large language models can summarize publicly available immigration information.

It **does not provide legal advice, immigration consultancy, or official guidance**.

AI-generated outputs may contain inaccuracies, omissions, or outdated information. Immigration laws and policies change frequently and vary by country. Users must **verify all information directly with official government sources or licensed immigration professionals** before making decisions.

Using this project does **not create an attorney-client or advisory relationship**, and the author assumes no liability for actions taken based on the generated outputs.

---

## Overview

The **AI Immigration & Citizenship Guidance Assistant** extracts readable text from official immigration webpages and uses an OpenAI model to generate a **clear, structured summary tailored to a user profile**.

The goal is to demonstrate how AI can help convert complex government policy pages into understandable guidance.

---

## Key Features

- Scrapes a single official immigration webpage  
- Extracts clean, visible text (no raw HTML sent to the model)  
- Accepts a custom immigration profile  
- Generates structured summaries including:
  - overview of the policy page  
  - eligibility requirements  
  - required documents  
  - timelines and next steps  
- Outputs results in clean Markdown format  

---

## How It Works

### 1. Scraping
- Requests one official government webpage  
- Parses HTML with **BeautifulSoup**  
- Removes scripts, styles, and non-visible elements  
- Extracts readable text

### 2. AI Analysis
- Sends page content and user profile to an OpenAI model  
- Generates a structured immigration summary  
- Formats output for readability

---


## Installation
pip install requests beautifulsoup4 openai python-dotenv 
OR
uv add requests beautifulsoup4 openai python-dotenv (If you are using uv)

## Environment Setup

Create a .env file:

OPENAI_API_KEY=your_api_key_here