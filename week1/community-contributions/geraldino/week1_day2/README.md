# WEEK 1 DAY 2 EXERCISE

A simple Python CLI application that fetches a website’s content and generates a short, snarky, humorous Markdown summary using a locally running Ollama model.

# 🚀 Features

Scrapes website content (removes scripts, styles, navigation, etc.)

Sends cleaned text to a local Ollama model

Generates:

    1.  A bold subject line

    2.  A short, humorous summary

    3.  Clean Markdown formatting

    4.  Works completely offline (after model is downloaded)

    5.  Automatically handles missing https://

## How It Works

    -   User inputs a website URL

    -   App fetches and cleans the webpage content

    -   Content is truncated to 2000 characters

    -   The cleaned text is sent to an Ollama LLM

    -   The model returns a Markdown-formatted summary

## Requirements

    -   Python 3.9+

    -   Ollama installed locally

    -   A downloaded model (e.g. llama3.2:1b)