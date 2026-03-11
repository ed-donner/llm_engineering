# Murat Community Insights

An AI-powered analysis tool that summarizes and analyzes projects inside the **community-contributions** directory of the **LLM Engineering** repository.

This project automatically generates structured summaries of each community contribution and extracts ecosystem-level insights using a Large Language Model (LLM).

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [File Overview](#file-overview)
- [How It Works](#how-it-works)
- [Example Summary Output](#example-summary-output)
- [Installation](#installation)
- [Environment Setup](#environment-setup)
- [Notes](#notes)
- [Future Improvements](#future-improvements)
- [Author](#author)

---

## Features

- Summarizes each contribution project
- Identifies project purpose and category
- Extracts visible technologies used
- Generates ecosystem insights across projects
- Detects recurring themes and standout contributions

---

## Project Structure

```
murat-community-insights/
├── README.md
└── week1/
    └── day1/
        ├── summarize_contributions.py
        ├── analyze_summaries.py
        ├── requirements.txt
        └── results/
            ├── community_contribution_summaries.json
            └── ecosystem_insights.md
```

---

## File Overview

**`summarize_contributions.py`**
Scans community contribution folders and generates summaries using an LLM.

**`analyze_summaries.py`**
Analyzes generated summaries and extracts ecosystem-level insights.

**`requirements.txt`**
Lists Python dependencies required to run the project.

**`results/`**
Stores generated outputs such as project summaries and analysis reports.

---

## How It Works

### Step 1 — Generate Project Summaries

The script scans the `community-contributions` directory and:

1. Extracts readable text from project folders
2. Sends content to an LLM
3. Generates structured summaries

Run:

```bash
python summarize_contributions.py
```

Output:

```
results/community_contribution_summaries.json
```

---

### Step 2 — Generate Ecosystem Insights

The second script analyzes all generated summaries to identify:

- Recurring project themes
- Interesting or innovative projects
- Beginner-friendly projects
- Commonly used technologies

Run:

```bash
python analyze_summaries.py
```

Output:

```
results/ecosystem_insights.md
```

---

## Example Summary Output

> **AI Clinical Trials Landscape Analyzer**
> A tool that analyzes clinical trial datasets to identify trends and insights using AI techniques for healthcare analytics.

> **Daily Kenyan News Summarizer**
> A system that collects trending Kenyan news articles and generates concise summaries using LLM-based summarization.

---

## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

Dependencies:

```
openai
python-dotenv
```

---

## Environment Setup

Create a `.env` file in the repository root:

```env
OPENAI_API_KEY=your_api_key_here
```

---

## Notes

- The script automatically skips the `murat-community-insights` folder to avoid analyzing itself.
- Generated files inside `results/` may change depending on the contributions present in the repository.

---

## Future Improvements

- Automatic project categorization
- Technology extraction and tagging
- Project similarity clustering
- Visualization dashboard for community insights

---

## Author

**Murat Kahraman**
Community contribution for the [LLM Engineering](https://github.com/ed-donner/llm_engineering) repository.