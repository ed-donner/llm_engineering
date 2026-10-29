# Corporate Intelligence and Strategic Brochure Studio

## Summary
Extends the Week 2 Day 2 Gradio lab from a basic landing page summarizer into an enterprise-grade multi-page intelligence studio built with Gradio Blocks (`gr.Blocks`).

## Key Innovations
1. **Autonomous Link Discovery:** Scans root domains and uses structured one-shot JSON prompting to identify and rank up to 4 strategic sub-pages (About, Pricing, Careers, Technology).
2. **Multi-Page Aggregation:** Recursively extracts and normalizes content across multiple domains with live progress tracking (`gr.Progress`).
3. **Audience-Driven Synthesis:** Dynamically adapts report structure and focus based on targeted reader personas (Investors, Enterprise Clients, Recruits, Partners).
4. **Gradio Blocks Layout:** Implements dual-column layout with real-time streaming, interactive telemetry logs, and instant Markdown export capabilities.
5. **Universal Client Architecture:** Supports production OpenAI configurations while maintaining full zero-cost compatibility with Google Gemini and OpenRouter free tiers.

## File Structure
- `corporate_intelligence_studio.ipynb`: Complete self-contained notebook containing system design, telemetry engine, and UI architecture.
- `scraper.py`: Web crawling and link extraction module.
- `README.md`: Architectural documentation and reproduction steps.