# Courtbee synthetic data generator

Week 3 exercise: https://github.com/SmarteventORG/courtbee-synth

Generates synthetic players and play invites for Courtbee, a booking platform for padel, pickleball and tennis clubs, behind a Gradio UI. It compares a Faker generator with an LLM generator: the LLM output is validated with Pydantic, validation errors are sent back to the model for a retry, and a Hugging Face embedding model scores how varied the generated texts are.

The LLM ran locally on Apple Silicon: Qwen3.8-27B (8-bit) served with mlx-lm for concurrent requests and with MTPLX for single requests. Any OpenAI-compatible endpoint works.
