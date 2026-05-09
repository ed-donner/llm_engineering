# LiveScore Web Scraper & AI Match Summarizer

## Overview

This project scrapes live football match data from livescore.com,
extracts visible text from dynamically rendered pages, and uses an
OpenAI model to generate a concise and structured summary of matches and
live scores.

The system is built as a Jupyter Notebook and demonstrates how web
scraping and large language models can be combined to transform raw web
data into clear, readable insights.

------------------------------------------------------------------------

## Key Features

-   Scrapes JavaScript-rendered pages using Selenium
-   Extracts clean page text only (no raw HTML parsing required)
-   Sends extracted content to an OpenAI model
-   Generates structured summaries
-   Uses tables where helpful for clarity
-   Notebook-based workflow for easy experimentation

------------------------------------------------------------------------

## Use Case

The primary goal is to:

-   Extract live match information
-   Identify teams, competitions, and scores
-   Summarize ongoing and completed matches
-   Present structured match data in a readable format

Example output includes:

### Executive Summary

-   Total live matches
-   Major competitions
-   Notable high-scoring games
-   Important match developments

### Live Matches Table

  Competition      Home Team   Away Team   Score   Status
  ---------------- ----------- ----------- ------- --------
  Premier League   Arsenal     Chelsea     2--1    78'
  La Liga          Madrid      Sevilla     1--0    HT

### Key Insights

-   Close contests
-   Dominant performances
-   Late goals or dramatic moments

------------------------------------------------------------------------

## Tech Stack

-   Python 3
-   Selenium
-   webdriver-manager
-   OpenAI Python SDK
-   Jupyter Notebook

------------------------------------------------------------------------

## Installation

Install dependencies:

    pip install selenium webdriver-manager openai

------------------------------------------------------------------------

## Environment Setup

Set your OpenAI API key before running the notebook.

### macOS / Linux

    export OPENAI_API_KEY="your_api_key_here"

### Windows (PowerShell)

    setx OPENAI_API_KEY "your_api_key_here"

Restart your terminal or notebook after setting the key.

------------------------------------------------------------------------

## How It Works

### 1. Scraping Phase

-   Headless Chrome loads the LiveScore page
-   JavaScript content renders fully
-   Visible page text is extracted
-   Raw HTML is not sent to the model

### 2. AI Summarization Phase

-   Page title, URL, and extracted text are sent to the model
-   The model returns a structured summary
-   Tables are used when useful for clarity

------------------------------------------------------------------------

## Limitations

-   LiveScore page structure may change
-   Excessive scraping may trigger rate limiting
-   Very large pages are truncated for token safety
-   Requires Chrome installed locally

------------------------------------------------------------------------

## Possible Improvements

-   Structured parsing of teams and scores before summarization
-   JSON output mode for programmatic consumption
-   Batch processing multiple competitions
-   Streamlit dashboard for live visualization
-   Scheduled scraping automation

------------------------------------------------------------------------

## Project File

web_scrape_openai_summary.ipynb

------------------------------------------------------------------------

## Purpose

This project demonstrates how web scraping and LLM-based summarization
can be combined to build lightweight sports intelligence tools for live
match tracking and analysis.
