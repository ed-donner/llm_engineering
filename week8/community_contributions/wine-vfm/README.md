# Wine Value Hunter — The Price is Right, adapted to wine 🍷

**Live demo:** https://gtraskas--wine-vfm-app-web.modal.run
**Repo:** https://github.com/gtraskas/wine-vfm

A full re-build of the week 8 agentic system in a new domain: instead of
estimating product prices from deals feeds, my agents hunt for **underpriced
wines in a live online shop**. Press the button on the demo and watch the
whole agent team work, with their logs streaming into the page.

## What's the same

The architecture follows the course: a fine-tuned open-source specialist
served on Modal, a RAG frontier agent over a Chroma vectorstore, a neural
network, an ensemble, a scanner with structured outputs, a messaging agent,
and a planning agent orchestrating them all — plus the Gradio finale.

## Where I diverged

- **Own dataset and target.** ~88K curated wine reviews (from ~281K raw), and
  a custom target: **VFM (value-for-money, 0-99)** = `log(points/price)`
  scaled on fixed analytic bounds — deterministic and reproducible from
  constants alone, no fitted scaler artifact.
- **QLoRA on Kaggle.** Llama 3.2 3B fine-tuned with rank-256 adapters in
  4-bit NF4 on a free T4 — including surviving a disk-full crash at 87% of
  the epoch and recovering the best checkpoint from the Hub's auto-pushes.
- **Regression-learned ensemble weights** fitted on held-out validation
  wines, instead of hardcoded blending.
- **A value-ranked scanner over a live shop.** The shop's listings print both
  critic score and price, so candidates are ranked by their *actual* VFM in
  pure Python before the LLM ever sees them — the LLM only extracts, it
  doesn't judge value.
- **The autonomous (tool-calling) planner runs in production.** The deployed
  app uses the LLM-driven planner; wines travel between tools by URL, so the
  ensemble always receives deterministically assembled text, never an LLM
  paraphrase (no train/inference skew).
- **On-demand instead of scheduled.** One button = one agentic run
  (~$0.10–0.25), on a scale-to-zero Modal deployment: a CPU container serves
  the UI and the GPU specialist wakes only when a hunt runs.

Thanks Ed — fantastic course. The "adapt it to your own domain" push is
where all the real learning happened.

— [Georgios Traskas](https://github.com/gtraskas)
