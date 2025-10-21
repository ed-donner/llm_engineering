# Multi-Agent Conversation Simulator (OpenAI + Ollama)

## Project Overview

This project is an experimental **multi-agent conversational simulation** built with **OpenAI GPT models** and a locally-hosted **Ollama LLM (Llama 3.2)**. It demonstrates how multiple AI personas can participate in a shared conversation, each with distinct roles, perspectives, and behaviors — producing a dynamic, evolving debate from different angles.

The script orchestrates a **three-way dialogue** around a single topic (“Why did the chicken cross the road?”) between three agents, each powered by a different model and persona definition:

- **Athena (OpenAI GPT-4o):** A strategic thinker who looks for deeper meaning, long-term consequences, and practical wisdom.
- **Loki (Ollama Llama 3.2):** A sarcastic trickster who mocks, questions, and challenges the others with wit and irony.
- **Orion (OpenAI GPT-4o):** A data-driven realist who grounds the discussion in facts, statistics, or logical deductions.

## What’s Happening in the Code

1. **Environment Setup**  
   - Loads the OpenAI API key from a `.env` file.  
   - Initializes OpenAI’s Python client and configures a local Ollama endpoint.

2. **Persona System Prompts**  
   - Defines system prompts for each agent to give them unique personalities and communication styles.  
   - These prompts act as the “character definitions” for Athena, Loki, and Orion.

3. **Conversation Initialization**  
   - Starts with a single conversation topic provided by the user.  
   - All three agents are aware of the discussion context and prior messages.

4. **Conversation Loop**  
   - The conversation runs in multiple rounds (default: 5).  
   - In each round:
     - **Athena (GPT)** responds first with a strategic viewpoint.
     - **Loki (Ollama)** replies next, injecting sarcasm and skepticism.
     - **Orion (GPT)** follows with a fact-based or analytical perspective.
   - Each response is appended to the conversation history so future replies build on previous statements.

5. **Dynamic Context Sharing**  
   - Each agent receives the **entire conversation so far** as context before generating a response.  
   - This ensures their replies are relevant, coherent, and responsive to what the others have said.

6. **Output Rendering**  
   - Responses are displayed as Markdown in a readable, chat-like format for each speaker, round by round.

## Key Highlights

- Demonstrates **multi-agent orchestration** with different models working together in a single script.
- Uses **OpenAI GPT models** for reasoning and **Ollama (Llama 3.2)** for local, cost-free inference.
- Shows how **system prompts** and **context-aware message passing** can simulate realistic dialogues.
- Provides a template for experimenting with **AI characters**, **debate simulations**, or **collaborative agent systems**.
