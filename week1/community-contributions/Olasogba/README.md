# Week 1 Exercise - Book Doctor Recommender

**Author:** Michael Akin-Ademola

## Description

A Book Doctor recommendation tool that demonstrates familiarity with both the OpenAI API and Ollama. This tool:
- Takes a user’s emotional state or current mood
- Generates book recommendations from both GPT-4o-mini and Llama 3.2
- Compares the two recommendation styles using GPT-5-nano
- Evaluates which response provides the most empathetic, relevant, and supportive book suggestions

The goal is to simulate a compassionate “Book Doctor” that prescribes books based on how someone is feeling.

## Features

- **Dual Model Recommendation**: Uses both OpenAI’s GPT-4o-mini and local Llama 3.2 to generate book suggestions
- **Streaming Output**: Displays recommendations in real-time as they are generated
- **Automated Comparison**: Uses GPT-5-nano to evaluate and rank both responses
- **Emotion-Aware Responses**: Focused on empathy, tone, and thoughtful book matching

## Evaluation Criteria

The comparison evaluates responses on:
1. **Emotional Attunement**: How well does the response acknowledge and validate the user’s feelings?
2. **Relevance of Recommendations**: How well do the books match the emotional state described?
3. **Clarity & Warmth**: Is the tone supportive, natural, and comforting?
4. **Explanation Quality**: Does it clearly explain why each book fits the situation?

## Files

- `week1_EXERCISE.ipynb` - Main notebook containing the Book Doctor implementation

## Usage

Simply modify the `question` variable with a description of how someone is feeling and the tool will:

1. Generate book recommendations from both models
2. Stream responses in real-time
3. Automatically compare and evaluate which recommendation is stronger and more emotionally aligned

## Requirements

- OpenAI API key
- Ollama running locally with llama3.2 model
- Python packages: openai, python-dotenv, IPython

