# Resume Role Suggestion with AI Agent

A Python CLI tool that analyzes a PDF resume and suggests relevant job titles using either:

- OpenAI API (cloud)
- Ollama local models (offline)

The output is returned in structured JSON format.

---

## Features

- Reads resume content from a `.pdf` file
- Uses LLM to generate suitable job roles
- Streams responses live in terminal
- Supports:
  - OpenAI API
  - Ollama local models
- Returns structured JSON output

---

## Requirements

- Python 3.9+
- pip
- Virtual environment (recommended)
- Optional: Ollama installed locally

---

## Installation

### Clone or Navigate to Project

```bash
cd your_project_directory
