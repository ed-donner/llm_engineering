# Implementation Plan - LLM Engineering Course

## Quick Reference
- **Current Phase**: Week 1 - Community Contributions (PR submitted)
- **Last Session**: 2026-03-17
- **Next Priority**: Monitor PR #2825 for Ed's feedback, continue with Week 2

---

## Project Goal

Complete the 8-week LLM Engineering course with hands-on projects and community contributions.

---

## Implementation Phases

### Phase 1: Week 1 - Fundamentals & First Project
- ✅ Set up development environment with uv
- ✅ Create Selenium-based web scraper for news sites
- ✅ Build sentiment analyzer using GPT-5-nano
- ✅ Add score reasoning explanation feature
- ✅ Submit PR to community-contributions (PR #2825)

### Phase 2: Weeks 2-4 - Core LLM Concepts
- ⬜ Week 2: Advanced prompting techniques
- ⬜ Week 3: Fine-tuning and embeddings
- ⬜ Week 4: RAG implementations with ChromaDB

### Phase 3: Weeks 5-7 - Applications
- ⬜ Week 5: Building applications with Gradio
- ⬜ Week 6: LangChain integrations
- ⬜ Week 7: GPU work on Google Colab

### Phase 4: Week 8 - Capstone
- ⬜ Build autonomous deal-finding agent
- ⬜ Deploy with Modal

---

## Session Progress Log

### Session 1: 2026-01-14
**Duration**: ~1 hour

**Completed**:
- [x] Created `day1_selenium_sentiment_analyzer.ipynb` in week1/community-contributions
- [x] Built SeleniumScraper class for JavaScript-rendered pages
- [x] Built SentimentAnalyzer class using GPT-5-nano
- [x] Added score_reasoning feature to explain sentiment scores
- [x] Tested scraping and analysis on Hacker News, TechCrunch, The Verge
- [x] Installed selenium and webdriver-manager dependencies
- [x] Updated CLAUDE.md with "Use Latest Technology" guidance

**Key Decisions**:
- Use `gpt-5-nano` as default model (latest cost-effective option)
- Include score_reasoning in output for transparency
- Use webdriver-manager for automatic ChromeDriver management

**Files Modified**:
- `week1/community-contributions/day1_selenium_sentiment_analyzer.ipynb` (new)
- `CLAUDE.md` (updated with latest tech guidance)
- `uv.lock` (added selenium, webdriver-manager)

**Next Session**:
- Run full analysis and verify output formatting
- Prepare and submit PR to Ed Donner's repository
- Continue with Week 1 exercises or move to Week 2

### Session 2: 2026-03-17
**Duration**: ~30 minutes

**Completed**:
- [x] Submitted clean PR #2825 for Selenium sentiment analyzer to ed-donner/llm_engineering
- [x] Created clean branch `selenium-sentiment-pr` from upstream main with only the notebook (565 lines, no outputs)
- [x] Closed incorrect PR #2824 (accidentally submitted Gemini integration instead) and deleted its remote branch

**Key Decisions**:
- Submit only the notebook file (no session management files, no README) to keep PR minimal
- Used `selenium-sentiment-analyzer` branch's clean version (outputs already cleared from earlier commits)

**Issues**:
- Initially submitted wrong content (Gemini integration from old PR #494 context) - caught and corrected by user

**Files in PR**:
- `week1/community-contributions/day1_selenium_sentiment_analyzer.ipynb`

**Next Session**:
- Monitor PR #2825 for Ed Donner's feedback
- Address any review comments
- Continue with Week 2 or other course work
