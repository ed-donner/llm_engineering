# Bruno's Week 1 Technical Tutor

This contribution is a personalized version of the week 1 exercise.

It builds a small technical tutor using:

- OpenAI `gpt-4o-mini` with streaming
- Local Ollama `llama3.2`
- A personalized tutor prompt
- A short multi-shot example to guide the answer style

The tutor is tuned for friendly, succinct explanations. It can use practical references to Godot/game development, PHP, or DevOps when those examples make the answer clearer.

Before running the notebook:

```bash
ollama pull llama3.2
ollama serve
```

Also make sure `OPENAI_API_KEY` is available in your `.env` file.
