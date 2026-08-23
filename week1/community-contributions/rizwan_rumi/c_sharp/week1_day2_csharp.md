# Week 1 Day 2 — C# Implementation

Continuing my C# (.NET) re-implementation of this course's exercises.

**Full source:** https://github.com/RizwanRumi/llm_engineering_with_c_sharp

## What's new

- Added **Ollama** as a third provider (alongside OpenAI and Claude), using its OpenAI-compatible endpoint at `http://localhost:11434/v1` — no new SDK needed.
- Generalized the exercise from an email subject-line generator into a **meeting notes summarizer**, to better showcase a general-purpose text generation task.
- Renamed classes accordingly: `ISubjectLineStrategy` → `ITextGenerationStrategy`, `SubjectLineGenerator` → `TextGenerator`, `SubjectGen*` → `TextGen*`.
- Restructured `Program.cs` into a thin dispatcher using a shared `IExercise` interface, so it can scale cleanly as more days/weeks are added without growing unmanageably.

See the [README](https://github.com/RizwanRumi/llm_engineering_with_c_sharp/blob/main/README.md) for setup and structure details.
