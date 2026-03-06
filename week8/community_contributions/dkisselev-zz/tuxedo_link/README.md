# 🎩 Tuxedo Link

**AI-Powered Cat Adoption Search Engine**

Find your perfect feline companion using AI, semantic search, and multi-platform aggregation.

*In loving memory of Kyra 🐱*

---

## 🌟 Overview

Tuxedo Link is an intelligent cat adoption platform that combines:

- **Natural Language Understanding** - Describe your ideal cat in plain English
- **Semantic Search with RAG** - ChromaDB + SentenceTransformers for personality-based matching
- **Multi-Modal Deduplication** - Uses CLIP for image similarity + text analysis
- **Hybrid Scoring** - 60% vector similarity + 40% attribute matching
- **Multi-Platform Aggregation** - Searches Petfinder and RescueGroups APIs
- **Serverless Architecture** - Optional Modal deployment with scheduled email alerts

**Tech Stack**: OpenAI GPT-4 • ChromaDB • CLIP • Gradio • Modal

---

## 📸 Application Screenshots

### 🔍 Search Interface
Natural language search with semantic matching and personality-based results:

![Search Interface](assets/1.%20search.png)

### 🔔 Email Alerts
Save your search and get notified when new matching cats are available:

![Alerts Management](assets/2.%20Alerts.png)

### 📖 About Page
Learn about the technology and inspiration behind Tuxedo Link:

![About Page](assets/3.%20About.png)

### 📧 Email Notifications
Receive beautiful email alerts with your perfect matches:

![Email Notification](assets/4.%20Email.png)

---

## 🚀 Full Project & Source Code

The complete source code, documentation, and setup instructions are available at:

### **[👉 GitHub Repository: dkisselev-zz/tuxedo-link](https://github.com/dkisselev-zz/tuxedo-link)**

The repository includes:

- ✅ Complete source code with 92 passing tests
- ✅ Comprehensive technical documentation (3,400+ lines)
- ✅ Agentic architecture with 7 specialized agents
- ✅ Dual vector store implementation (main + metadata)
- ✅ Modal deployment guide for production
- ✅ Setup scripts and configuration examples
- ✅ LLM techniques documentation (structured output, RAG, hybrid search)

---

## 🧠 Key LLM/RAG Techniques

### 1. Structured Output with GPT-4 Function Calling
Extracts search preferences from natural language into Pydantic models

### 2. Dual Vector Store Architecture
- **Main ChromaDB** - Cat profile semantic embeddings
- **Metadata DB** - Fuzzy color/breed matching with typo tolerance

### 3. Hybrid Search Strategy
Combines vector similarity (60%) with structured metadata filtering (40%)

### 4. 3-Tier Semantic Normalization
Dictionary → Vector DB → Fuzzy fallback for robust term mapping

### 5. Multi-Modal Deduplication
Fingerprint + text (Levenshtein) + image (CLIP) similarity scoring

---

## 🏆 Project Highlights

- **92 Tests** - 81 unit + 11 integration tests (100% passing)
- **Production Ready** - Serverless Modal deployment with volumes
- **Email Alerts** - Scheduled background jobs for new match notifications
- **95%+ Accuracy** - Multi-modal deduplication across platforms
- **85-90% Match Quality** - Hybrid scoring algorithm

---

## 📚 Documentation

- **TECHNICAL_REFERENCE.md** - Complete API documentation
- **MODAL_DEPLOYMENT.md** - Cloud deployment guide
- **ARCHITECTURE_DIAGRAM.md** - System architecture visuals
- **tests/README.md** - Testing guide and coverage

---

<div align="center">

**Made with ❤️ in memory of Kyra**

*May every cat find their perfect home* 🐾

**[View Full Project on GitHub →](https://github.com/dkisselev-zz/tuxedo-link)**

</div>
