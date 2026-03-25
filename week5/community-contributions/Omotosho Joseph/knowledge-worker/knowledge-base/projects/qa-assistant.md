# Technical Q&A Assistant - Project Documentation

## Overview
A multi-model AI assistant that answers technical programming questions. Built with Python, Gradio, and multiple LLM providers.

## Architecture
- **Frontend**: Gradio ChatInterface with streaming support
- **Backend**: Python with OpenAI SDK using the OpenAI-compatible client pattern
- **Models**: GPT-4o-mini (OpenAI), Claude (OpenRouter), Llama 3.2 (Ollama)
- **Tools**: Stack Overflow search integration via agentic loop

## Key Features
1. **Streaming Responses**: Real-time token-by-token output using yield generators
2. **Multi-Model Switching**: Same OpenAI class, different base_url for each provider
3. **System Prompts**: Carefully crafted prompts for technical expertise
4. **Tool Calling**: Stack Overflow search demonstrates a full agentic loop where the LLM decides when to use external tools

## How It Works
The user asks a technical question. The system prompt establishes the assistant as a coding expert. If the LLM determines it needs more information, it calls the Stack Overflow search tool. The tool results are fed back into the conversation, and the LLM synthesizes a final answer. This is the agentic loop pattern.

## Setup
Requires: OpenAI API key, OpenRouter API key, Ollama running locally with Llama 3.2 pulled.

## Lessons Learned
- The OpenAI-compatible client pattern is incredibly powerful for provider switching
- Streaming significantly improves user experience for long responses
- System prompts are the cheapest way to improve output quality
- Tool calling turns a simple chatbot into a capable agent
