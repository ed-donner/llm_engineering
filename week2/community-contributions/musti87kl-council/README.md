# Council of LLMs (Week 2, Days 1-3)

Two small LiteLLM projects, split into config / personas / chat / main files.

- `three_way_chat/` (Day 1): GPT and Claude debate football, Llama judges. Prints each reply with its cost. Run `python main.py`.
- `council_app/` (Days 2-3): a Gradio page where you design the scene. Each of the 3 seats (two debaters and a judge) gets a model, a name, a purpose and a rule. The judge ends the debate by writing `LOSER: <name>`, or it stops after 5 rounds. Run `python app.py`.
- `council_explainer.ipynb`: how the hidden system prompts and the resent transcript work.

Needs `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` in `.env`, and Ollama with `llama3.2` for the Llama seat.

Finding: Llama 3.2 as judge often names a loser after one round; GPT as judge waits for real evidence.
