# Local LLM CVE Analyzer for DevSecOps

A powerful, entirely local open-source tool that uses the NIST NVD API and local Language Models (via [Ollama](https://ollama.com/)) to automatically fetch, analyze, and generate commercially usable **Secure Development Lifecycle (SDL)** summaries for CVE vulnerabilities.

## Why this project?
Reading raw CVE descriptions from the National Vulnerability Database (NVD) can be vague or purely descriptive. As an Application Security Engineer or DevSecOps Architect, you need **actionable** instructions for developers. 

This tool automates that process. It securely feeds raw CVE data into a local LLM, forcing the AI to act as a DevSecOps Architect and output specific, architectural remediation steps and DAST/SAST integration guidelines. And because it uses local LLMs, **zero proprietary data is leaked to external cloud providers**.

## Features

- **Direct NVD API Integration:** Fetches up-to-date CVE descriptions, CVSS scores, and attack vectors.
- **100% Local Processing:** Uses Ollama to run models like LLaMA 3, Gemma 2, or Mistral locally on your machine.
- **Structured SDL Reports:** Transforms vague CVE descriptions into actionable reports containing:
  - Executive Summaries
  - Technical Threats & Exploitability
  - Business Impacts
  - Developer Remediation Strategies
  - Prevention & SDL Guardrails

## Prerequisites

To run this tool, you need:
1. **Python 3.12+**
2. **[Ollama](https://ollama.com/)** running locally on your machine.
3. At least one open-source model pulled in Ollama. For example:
   ```bash
   ollama pull gemma2:2b
   # or
   ollama pull llama3.2
   ```

## Installation

1. Clone or download the repository to your local machine:
   ```bash
   git clone https://github.com/your-username/local-cve-analyzer.git
   cd local-cve-analyzer
   ```

2. Install the required Python packages:
   ```bash
   pip install requests ollama ipython
   ```

## Usage

### As a standalone script
You can edit the `if __name__ == "__main__":` block inside `cve_analyzer.py` then run the script directly in your terminal:

```bash
python cve_analyzer.py
```

### Inside a Jupyter Notebook
This tool was built to integrate smoothly into interactive notebooks. Drop this into a Jupyter cell:

```python
from cve_analyzer import CVESecurityAnalyzer
from IPython.display import display, Markdown

# Initialize the analyzer specifying your preferred local model
analyzer = CVESecurityAnalyzer(model_name="gemma2:2b")

# Analyze a vulnerability (e.g., Log4Shell)
report = analyzer.generate_sdl_report("CVE-2021-44228")

# Display neatly formatted Markdown
display(Markdown(report))
```
### Ideas for future contributions:
- Add multi-threading/async support for scanning multiple CVEs simultaneously.
- Enhance fallback logic when the NVD API rate-limits the user.
- Add support for generating reports as PDF or exporting directly to Jira APIs.
