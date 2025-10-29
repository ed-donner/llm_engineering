## 🚀 Modal Deployment Guide

How to deploy Tuxedo Link to Modal for production use.

---

## 🏗️ Production Architecture

In production mode, Tuxedo Link uses a **hybrid architecture**:

### Component Distribution

**Local (Your Computer)**:
- Gradio UI (`app.py`) - User interface only
- No heavy ML models loaded
- Fast startup

**Modal (Cloud)**:
- `modal_api.py` - Main API functions (profile extraction, search, alerts)
- `scheduled_search.py` - Scheduled jobs (daily/weekly alerts, cleanup)
- Database (SQLite on Modal volume)
- Vector DB (ChromaDB on Modal volume)
- All ML models (GPT-4, SentenceTransformer, CLIP)

### Communication Flow

```
User → Gradio UI (local) → modal.Function.from_name().remote() → Modal API → Response → UI
```

**Key Functions Exposed by Modal**:
1. `extract_profile` - Convert natural language to CatProfile
2. `search_cats` - Execute complete search pipeline
3. `create_alert_and_notify` - Create alert with optional immediate email
4. `get_alerts` / `update_alert` / `delete_alert` - Alert management

---

## 📋 Quick Start (Automated Deployment)

The easiest way to deploy is using the automated deployment script:

```bash
cd week8/community_contributions/dkisselev-zz/tuxedo_link

# 1. Configure config.yaml for production
cp config.example.yaml config.yaml
# Edit config.yaml and set deployment.mode to 'production'

# 2. Ensure environment variables are set
# Load from .env or set manually:
export OPENAI_API_KEY=sk-...
export PETFINDER_API_KEY=...
export PETFINDER_SECRET=...
export RESCUEGROUPS_API_KEY=...
export MAILGUN_API_KEY=...

# 3. Run deployment script
./deploy.sh
```

The script will automatically:
- ✅ Validate Modal authentication
- ✅ Check configuration
- ✅ Create/update Modal secrets
- ✅ Create Modal volume
- ✅ Upload config.yaml to Modal
- ✅ Deploy scheduled search services