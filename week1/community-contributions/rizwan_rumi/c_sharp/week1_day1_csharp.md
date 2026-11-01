# Week 1 Day 1 — C# Implementation

I've been re-implementing this course's exercises in C# (.NET) as a way to practice the same LLM engineering concepts outside Python, while also comparing multiple LLM providers side by side.

**Full source and ongoing exercises:**
https://github.com/RizwanRumi/llm_engineering_with_c_sharp

## Week 1 Day 1: Email Subject Line Generator

Given the body of an email, the program suggests a short, professional subject line for it — the "try yourself" exercise from `day1.ipynb`, ported to C#.

**Implemented for both OpenAI and Anthropic (Claude)**, using the official `OpenAI` and `Anthropic` .NET SDKs.

The provider-selection logic uses the **Strategy design pattern**:
- `ISubjectLineStrategy` — a common interface for generating a subject line from email text
- `OpenAiSubjectLineStrategy` / `ClaudeSubjectLineStrategy` — one concrete implementation per provider
- `SubjectLineGenerator` — a small context class that wraps whichever strategy is selected

At runtime, the user is prompted to choose a provider (OpenAI or Claude), and the same generation flow runs regardless of which one is picked — new providers can be added later without touching the existing code.

The repo also keeps the original, single-provider versions (`SubjectGenOpenAI.cs`, `SubjectGenClaude.cs`) alongside the Strategy pattern version, as a before/after reference for anyone curious what the refactor actually simplifies.

See the [README](https://github.com/RizwanRumi/llm_engineering_with_c_sharp/blob/main/README.md) in the repo for setup instructions and further details.
