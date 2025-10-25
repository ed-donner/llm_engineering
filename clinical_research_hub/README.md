# AI-Powered Clinical Research Intelligence Hub

An advanced automated pipeline that discovers, analyzes, and curates cutting-edge AI applications in clinical research using **Qwen LLM** (via OpenRouter), featuring a premium glassmorphism web interface with comprehensive UI/UX enhancements.

## 🚀 Overview

This project demonstrates advanced LLM engineering patterns for building production-ready AI applications, including:
- Multi-source data aggregation from 12+ trusted medical/research sources
- Intelligent content filtering and categorization using Qwen LLM
- Automated summarization with dynamic writing styles
- Premium interactive web interface with modern design patterns
- Production deployment workflows with GitHub Actions

## ✨ Key Features

### Intelligence Pipeline
- **Automated Content Discovery**: Monitors PubMed, Clinical Trials.gov, Nature Medicine, NEJM AI, The Lancet Digital Health, and more
- **AI-Powered Analysis**: Uses Qwen LLM (via OpenRouter) to analyze and categorize articles by 6 specific AI technology types
- **Smart Filtering**: Multi-tier content validation to identify AI applications in clinical research
- **Accurate Date Parsing**: Advanced date extraction with support for relative dates and multiple metadata fields
- **Multi-format Output**: Generates both JSON data and premium styled HTML presentations
- **Daily Automation**: GitHub Actions workflow for weekday automation (Mon-Fri 5 AM CET)

### Premium Web Interface
- **Glassmorphism Design**: Modern UI with frosted glass effects, animated gradients, and floating elements
- **Interactive Filtering**: Real-time filtering by 6 AI technology categories with horizontal scrolling pills
- **Advanced Search**: Debounced search (150ms) with highlighting, XSS protection, and multi-criteria filtering
- **Mobile-First Design**: Comprehensive mobile optimization with iOS safe-area support and momentum scrolling
- **Full Accessibility**: WCAG compliance with screen reader support, keyboard navigation (/ to focus, Esc to clear), and semantic HTML
- **URL State Management**: Shareable links with preserved search/filter state

### AI Technology Categories

The system categorizes discoveries across 6 key domains:

1. **🤖 Generative AI** - LLMs, ChatGPT, text generation applications
2. **💬 Natural Language Processing** - Text analysis, clinical notes processing
3. **🧠 Machine Learning** - Predictive models, algorithms, ML techniques
4. **📱 Digital Health** - Health apps, digital therapeutics, connected devices
5. **🎯 Trial Optimization** - Clinical trial design, patient recruitment, protocol optimization
6. **⚖️ AI Ethics** - Bias, fairness, transparency, responsible AI implementation

## 🛠️ Technical Implementation

### Core Components

- **`pipeline.py`** - Main processing pipeline with:
  - Multi-source RSS feed aggregation
  - Google Custom Search integration
  - PubMed, Europe PMC, and Semantic Scholar API clients
  - Token bucket rate limiting for API reliability
  - Exponential backoff with jitter for HTTP retries
  - Atomic file writes and schema validation
  
- **`qwen_client.py`** - LLM client wrapper providing:
  - OpenRouter API integration for Qwen models
  - Retry logic with exponential backoff
  - Cost tracking and usage monitoring
  - Error handling and logging

- **`templates/index.html`** - Premium UI template with:
  - Alpine.js for reactive interactions
  - Tailwind CSS for utility-first styling
  - Custom glassmorphism effects and animations
  - XSS-protected search highlighting
  - Mobile-optimized responsive design

- **`.github/workflows/deploy.yml`** - Automated deployment:
  - Scheduled runs Monday-Friday at 5:00 AM CET
  - GitHub Pages deployment with gh-pages branch
  - Environment variable management for API keys
  - Optional analytics integration (GoatCounter)

### Production Features

- **Rate Limiting**: Token bucket implementation to prevent API 429 errors
- **Error Handling**: Comprehensive error handling with graceful degradation
- **Data Validation**: Pydantic models for schema validation
- **Security**: XSS protection, safe HTML escaping, secure search highlighting
- **Monitoring**: Detailed logging with separate log files per run
- **Performance**: Debounced search, efficient DOM updates, reduced motion support

## 📊 Performance Metrics

Based on production runs:
- **Articles Processed**: 180+ per run from comprehensive source network
- **AI-Relevant Discoveries**: 16 high-quality articles (8.9% precision)
- **Cost Efficiency**: ~$0.10 per complete content curation run
- **Source Distribution**: Google Scholar, PubMed (20 API calls), Europe PMC, Semantic Scholar, RSS feeds
- **Rate Limiting**: Successfully manages API constraints with exponential backoff

## 🎨 UI/UX Highlights

- **14 Comprehensive Enhancements**:
  - Debounced search with 150ms delay
  - Keyboard navigation (/ to focus, Escape to clear)
  - Skip-to-content accessibility links
  - Reduced motion support for better battery life
  - URL state persistence for shareable links
  - Advanced sorting controls (newest/oldest/source)
  - Live region announcements for screen readers
  - Copy link functionality with fallbacks
  - Back-to-top button with smooth scrolling
  - Enhanced semantic HTML with time elements
  - Focus-visible styles for keyboard navigation
  - Improved color contrast for WCAG compliance
  - Mobile-optimized layouts with horizontal scrolling
  - iOS safe-area support and momentum scrolling

## 🔧 Setup & Installation

1. **Install dependencies**
```bash
cd clinical_research_hub
pip install -r requirements.txt
```

2. **Set environment variables**
```bash
export OPENROUTER_API_KEY="your-openrouter-api-key-here"
# Optional (Google Custom Search for broader discovery)
export GOOGLE_API_KEY="your-google-api-key"
export GOOGLE_CX="your-google-cse-id"
# Optional (privacy-friendly analytics)
export GOATCOUNTER_URL="https://YOURCODE.goatcounter.com/count"
```

3. **Run the pipeline**
```bash
python pipeline.py
```

The pipeline generates:
- **JSON briefs** with structured data (`briefs/YYYY-MM-DD.json`)
- **HTML interface** with interactive filtering (`site/index.html`)
- **Detailed logs** (`logs/YYYY-MM-DD.log`)

## 📅 Deployment

### GitHub Actions Automation

The included workflow file (`.github/workflows/deploy.yml`) enables:
- **Automated Runs**: Monday-Friday at 5:00 AM CET
- **GitHub Pages**: Automatic deployment to gh-pages branch
- **Environment Management**: Secure API key handling via repository secrets
- **Manual Triggers**: On-demand runs via Actions interface

### Required Repository Secrets

Add these in Settings → Secrets and variables → Actions:
- `OPENROUTER_API_KEY` (required)
- `GOOGLE_API_KEY` (optional)
- `GOOGLE_CX` or `GOOGLE_CSE_ID` (optional)
- `GOATCOUNTER_URL` (optional)

## 📁 Repository Structure

```
clinical_research_hub/
├── pipeline.py              # Main processing script
├── qwen_client.py           # Qwen LLM client wrapper
├── generate_html.py         # HTML generation script
├── site_config.py          # Site configuration
├── requirements.txt         # Python dependencies
├── environment.yml          # Conda environment
├── templates/              # Jinja2 templates
│   └── index.html          # Main UI template
└── .github/workflows/
    └── deploy.yml          # Automated deployment workflow
```

## 🔗 Live Demo

See the project in action: [AI Clinical Research Hub](https://albertoclemente.github.io/ai-clinicalresearch-hub/)

## 📝 Use Cases

This project is ideal for:
- **Researchers**: Tracking latest AI developments in clinical research
- **Clinicians**: Discovering AI tools and applications for practice
- **AI Practitioners**: Understanding real-world medical AI implementations
- **Educators**: Teaching LLM engineering and production deployment patterns

## 🎓 Learning Outcomes

This project demonstrates:
- Multi-source data aggregation and ETL pipelines
- LLM-powered content analysis and categorization
- Production-ready API rate limiting and error handling
- Modern web UI development with progressive enhancement
- Automated deployment and CI/CD workflows
- Accessibility and mobile-first design patterns
- Security best practices (XSS protection, data validation)

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

Built as a contribution to the LLM Engineering community, demonstrating advanced patterns for production AI applications.
