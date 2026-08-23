# Week 1 Exercise - Tech Question Explainer

**Author:** Philip Omoigui

## Description

A technical question explainer tool that demonstrates familiarity with both OpenAI API and Ollama. This tool:

- Takes a technical question
- Gets responses from both GPT-4o-mini and Llama 3.2
- Compares the two responses using GPT-5-nano
- Evaluates which explanation is better for beginners

## Features

- **Dual Model Response**: Uses both OpenAI's GPT-4o-mini and local Llama 3.2
- **Streaming Output**: Real-time display of responses as they're generated
- **Automated Comparison**: Uses GPT-5-nano to evaluate and rank both responses
- **Beginner-Focused**: Optimized for educational content with clear, beginner-friendly explanations

## Evaluation Criteria

The comparison evaluates responses on:
1. **Beginner Friendliness** - How easy is it for a beginner to understand?
2. **Tackles Main Point** - How well does it address the core concept?
3. **Clear Examples** - How effective are the examples and explanations?

## Files

- `week1_EXERCISE.ipynb` - Main notebook with the tech explainer implementation

## Usage

Simply modify the `question` variable with your technical question, and the tool will:
1. Generate explanations from both models
2. Stream the responses in real-time
3. Automatically compare and evaluate which explanation is better

## Requirements

- OpenAI API key
- Ollama running locally with llama3.2 model
- Python packages: openai, python-dotenv, IPython

