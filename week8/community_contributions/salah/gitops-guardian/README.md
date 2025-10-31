# GitOps Guardian

AI-powered multi-agent system for automated security and compliance review of GitOps pull requests.

## What It Does

GitOps Guardian automatically reviews pull requests in GitOps repositories to identify security risks and compliance violations before code reaches production. It uses a multi-agent architecture combining AI-powered security analysis with rule-based Kubernetes best practices validation.

## Key Features

- **Multi-Agent Architecture**: Four specialized agents (Scanner, Security, Compliance, Ensemble)
- **Security Detection**: Identifies hardcoded secrets, privileged containers, missing security contexts, insecure RBAC
- **Compliance Validation**: Checks for :latest tags, missing resource limits, required labels
- **Risk Scoring**: 0-1 risk score with SAFE/REVIEW/RISKY classification
- **Interactive Dashboard**: Real-time Gradio web interface
- **Cost Tracking**: Monitor OpenAI API costs (~$0.0004 per PR)
- **Export & Comments**: Download results as JSON/CSV, post reviews to GitHub PRs
- **Historical Trends**: Track risk scores over time

## Requirements

- Python 3.10+
- GitHub Personal Access Token (repo read permissions)
- OpenAI API Key
- GitOps repositories with open pull requests

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your tokens and repository list
```

3. Run the application:
```bash
python app.py
```

4. Open browser at `http://localhost:7860`

## Configuration

Create `.env` file with:
```bash
GITHUB_TOKEN=ghp_your_token
OPENAI_API_KEY=sk_your_key
GITOPS_REPOS=owner/repo1,owner/repo2
```

## Project Structure

```
gitops-guardian/
├── models.py          # Pydantic data models
├── agents.py          # Multi-agent system (4 agents)
├── app.py             # Gradio UI & orchestration
├── requirements.txt   # Dependencies
└── .env.example       # Configuration template
```

## How It Works

1. **Scanner Agent** fetches open PRs from GitHub repositories
2. **Security Agent** analyzes diffs using OpenAI GPT-4o-mini for security issues
3. **Compliance Agent** validates Kubernetes manifests against best practices
4. **Ensemble Agent** combines scores (60% security, 40% compliance) into overall risk
5. Results displayed in dashboard with recommendations

## Week 8 Concepts Applied

- Multi-agent system with base Agent class and color-coded logging
- Ensemble pattern with weighted scoring
- External API integration (GitHub + OpenAI)
- Pydantic models for type safety
- Gradio web interface
- Persistent memory (JSON-based)
- Real-world DevOps use case

## Author

Salah - Week 8: Multi-Agent Systems - LLM Engineering Bootcamp 2025
