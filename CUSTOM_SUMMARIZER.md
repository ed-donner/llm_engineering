# Local Notebook Summarizer 🤖

A lightweight developer tool that automatically parses local Jupyter Notebooks (`.ipynb`) and uses Large Language Models to generate clean, structured Markdown summaries of daily learnings and code experiments.

## System Architecture

Here is how the data flows from the local environment to the LLM and back:

```mermaid
graph TD
    A[Local Jupyter Notebook] -->|fetch_notebook_contents| B(JSON Parser)
    B -->|Extract Code & Markdown| C{Text Compiler}
    C -->|Format System Prompt| D[OpenAI API]
    D -->|gpt-4o-mini| E[Formatted Markdown Summary]
    
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style D fill:#bbf,stroke:#333,stroke-width:2px
    style E fill:#bfb,stroke:#333,stroke-width:2px