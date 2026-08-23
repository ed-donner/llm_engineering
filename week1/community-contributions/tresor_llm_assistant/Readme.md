# 📗 Table of Contents

- [📗 Table of Contents](#-table-of-contents)
- [📖 Tresor LLM Assistant](#about-project)
  - [🛠 Built With](#-built-with)
    - [Tech Stack](#tech-stack)
    - [Key Features](#key-features)
  - [💻 Getting Started](#-getting-started)
    - [Prerequisites](#prerequisites)
    - [Install](#install)
    - [Usage](#usage)
  - [👥 Authors](#-authors)
  - [🔭 Future Features](#-future-features)
---

# 📖 Tresor LLM Assistant <a name="about-project"></a>

LLM Assistant is a **multi-capability AI engine** powered by local LLMs via **Ollama**.

It provides a unified interface to perform tasks such as:
- Text summarization
- Classification
- Translation
- Sentiment analysis
- SQL generation
- Meeting minutes extraction
- Entity extraction
- Website content analysis and summary

The goal of this project is to demonstrate how LLMs can be structured into a reusable and extensible **AI utility toolkit** suitable for real-world applications like CRM, ERP, and automation systems.

---

## 🛠 Built With <a name="built-with"></a>

### Tech Stack <a name="tech-stack"></a>

<details>
  <summary>Backend / Core</summary>
  <ul>
    <li>Python</li>
    <li>Ollama (Local LLM runtime)</li>
    <li>OpenAI Python SDK (OpenAI-compatible API)</li>
    <li>BeautifulSoup (web scraping)</li>
    <li>Requests (HTTP calls)</li>
  </ul>
</details>

---

### Key Features <a name="key-features"></a>

- Multi-task LLM assistant
- Text summarization
- Text classification
- Translation support
- Text rewriting (style adaptation)
- JSON structured extraction
- Sentiment analysis
- SQL query generation
- Meeting minutes extraction
- Named entity extraction
- Website content analysis and 
---

## 💻 Getting Started <a name="getting-started"></a>

To get a local copy up and running, follow these steps.

---

### Prerequisites

In order to run this project you need:

- Python 3.9+
- Ollama installed and running locally
- A model pulled (e.g. `llama3.2`)
- Terminal / Command line
- IDE (e.g. VS Code)

---

### Install

Install this project with:


```sh
  Follow the documentation of the current project by installing all needed tools
```

### Run Ollama
Make sure Ollama is running and the model is available
```sh
ollama serve

ollama pull llama3.2
```

### Usage

Run the application:

```sh
  python main.py
```
Open your terminal to see outputs for:

- Summarization
- Classification
- Translation
- Sentiment analysis
- SQL generation
- Meeting minutes
- Entity extraction

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- AUTHORS -->

## 👥 Authors <a name="authors"></a>

👤 **Tresor Sawasawa**

- GitHub: [@tresorsawasawa](https://github.com/tresorsawasawa)
- Twitter: [@TresorSawasawa](https://x.com/TresorSawasawa)
- LinkedIn: [@Trésor Sawasawa](https://www.linkedin.com/in/tresor-sawasawa/)


<p align="right">(<a href="#readme-top">back to top</a>)</p>


## 🔭 Future Features <a name="future-features"></a>

- CLI interface for direct terminal commands
- FastAPI REST API wrapper
- Structured JSON validation using Pydantic
- Streaming responses from LLM
- Configurable prompt templates (YAML/JSON)
- Logging and monitoring layer
- Plugin system for custom tasks

<p align="right">(<a href="#readme-top">back to top</a>)</p>
