# 🎩 Tuxedo Link

**AI-Powered Cat Adoption Search Engine**

Find your perfect feline companion using AI, semantic search, and multi-platform aggregation.

*In loving memory of Kyra 🐱*

---

## 🌟 Features

✅ **Multi-Platform Search** - Aggregates from Petfinder and RescueGroups  
✅ **Natural Language** - Describe your ideal cat in plain English  
✅ **Semantic Matching** - AI understands personality, not just keywords  
✅ **Color/Breed Matching** - 3-tier system handles typos ("tuxado" → "tuxedo", "main coon" → "Maine Coon")  
✅ **Deduplication** - Multi-modal (name + description + image) duplicate detection  
✅ **Hybrid Search** - Combines vector similarity with structured filters  
✅ **Image Recognition** - Uses CLIP to match cats visually  
✅ **Email Notifications** - Get alerts for new matches  
✅ **Serverless Backend** - Optionally deploy to Modal for cloud-based search and alerts

**Technical Stack**: OpenAI GPT-4 • ChromaDB • CLIP • Gradio • Modal

## 🏗️ Architecture Modes

Tuxedo Link supports two deployment modes:

### Local Mode (Development)
- All components run locally
- Uses local database and vector store
- Fast iteration and development
- No Modal required

### Production Mode (Cloud)
- UI runs locally, backend runs on Modal
- Database and vector store on Modal volumes
- Scheduled email alerts active
- Scalable and serverless

Switch between modes in `config.yaml` by setting `deployment.mode` to `local` or `production`.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- `uv` package manager
- API keys (OpenAI, Petfinder, Mailgun)
### Installation

1. **Navigate to project directory**
```bash
cd week8/community_contributions/dkisselev-zz/tuxedo_link
```

2. **Set up virtual environment**
```bash
uv venv
source .venv/bin/activate 
uv pip install -e ".[dev]"
```

3. **Configure environment variables**
```bash
# Copy template and add your API keys
cp env.example .env
# Edit .env with your keys
```

4. **Configure application settings**
```bash
# Copy configuration template
cp config.example.yaml config.yaml
# Edit config.yaml for email provider and deployment mode
```

5. **Initialize databases**
```bash
python setup_vectordb.py
```

6. **Run the application**
```bash
./run.sh
```

Visit http://localhost:7860 in your browser!

---

## 🔑 API Setup

### Required API Keys

Add these to your `.env` file:

```bash
# OpenAI (for profile extraction)
# Get key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-...

# Petfinder (for cat listings)
# Get key from: https://www.petfinder.com/developers/
PETFINDER_API_KEY=your_key
PETFINDER_SECRET=your_secret

# Mailgun (for email alerts)
# Get key from: https://app.mailgun.com/
MAILGUN_API_KEY=your_mailgun_key
```

### Optional API Keys

```bash
# RescueGroups (additional cat listings)
# Get key from: https://userguide.rescuegroups.org/
RESCUEGROUPS_API_KEY=your_key

# SendGrid (alternative email provider)
SENDGRID_API_KEY=SG...

# Modal (for cloud deployment)
MODAL_TOKEN_ID=...
MODAL_TOKEN_SECRET=...
```

### Application Configuration

Edit `config.yaml` to configure:

```yaml
# Email provider (mailgun or sendgrid)
email:
  provider: mailgun
  from_name: "Tuxedo Link"
  from_email: "noreply@yourdomain.com"

# Mailgun domain
mailgun:
  domain: "your-domain.mailgun.org"

# Deployment mode (local or production)
deployment:
  mode: local  # Use 'local' for development
```

**Note**: API keys go in `.env` (git-ignored), application settings go in `config.yaml` (also git-ignored).

---

## 💻 Usage

### Search Tab
1. Describe your ideal cat in natural language
2. Click "Search" or press Enter
3. Browse results with match scores
4. Click "View Details" to see adoption page

**Example queries:**
- "I want a friendly family cat in NYC good with children"
- "Looking for a playful young kitten"
- "Show me calm adult cats that like to cuddle"
- "Find me a tuxedo maine coon in Boston" (natural color/breed terms work!)
- "Orange tabby that's good with other cats"

#### Alerts Tab
1. Perform a search in the Search tab first
2. Go to Alerts tab
3. Enter your email address
4. Choose notification frequency (Immediately, Daily, Weekly)
5. Click "Save Alert"

You'll receive email notifications when new matches are found!

#### About Tab
Learn about Kyra and the technology behind the app

### Development Mode

For faster development and testing, use local mode in `config.yaml`:

```yaml
deployment:
  mode: local  # Uses local database and cached data
```

## 📚 Documentation

### Complete Technical Reference

For detailed documentation on the architecture, agents, and every function in the codebase, see:

**[📖 TECHNICAL_REFERENCE.md](docs/TECHNICAL_REFERENCE.md)** - Complete technical documentation including:
- Configuration system
- Agentic architecture
- Data flow pipeline
- Deduplication strategy
- Email provider system
- Alert management
- All functions with examples
- User journey walkthroughs

**[📊 ARCHITECTURE_DIAGRAM.md](docs/architecture_diagrams/ARCHITECTURE_DIAGRAM.md)** - Visual diagrams:
- System architecture
- Agent interaction
- Data flow
- Database schema

**[🚀 MODAL_DEPLOYMENT.md](docs/MODAL_DEPLOYMENT.md)** - Cloud deployment guide:
- Production mode architecture
- Automated deployment with `deploy.sh`
- Modal API and scheduled jobs
- UI-to-Modal communication
- Monitoring and troubleshooting

**[🧪 tests/README.md](tests/README.md)** - Testing guide:
- Running unit tests
- Running integration tests
- Manual test scripts
- Coverage reports

---

## 🤝 Contributing

This project was built as part of the Andela LLM Engineering bootcamp. Contributions and improvements are welcome!

---

## 📄 License

See [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ in memory of Kyra**

*May every cat find their perfect home* 🐾

[Technical Reference](docs/TECHNICAL_REFERENCE.md) • [Architecture](docs/architecture_diagrams/ARCHITECTURE_DIAGRAM.md) • [Deployment](docs/MODAL_DEPLOYMENT.md) • [Tests](tests/README.md)

</div>
