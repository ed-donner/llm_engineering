# C++ Code Generator

## Overview
a modular notebook for generating optimized C++ from Python with a frontier model, including optional compile and benchmark helpers.

## Features
- Convert Python code or natural language description to optimized C++
- Option to optimize for speed and memory
- Compile generated C++ code and capture output/errors
- Benchmark compiled binary and report execution time
- Modular Gradio UI for all steps
- Secure token loading from HF_TOKEN environment variable

## Technical Details
- Single-file Gradio app (notebook or app.py)
- Uses HuggingFace chat_completion endpoint for instruct models
- Compile and benchmark helpers using subprocess

## Requirements
- Python packages: gradio, requests, python-dotenv
- HuggingFace account and HF_TOKEN set in environment
- g++ compiler installed

## Setup
1. Install dependencies:
   ```bash
   pip install gradio requests python-dotenv
   ```
2. Set up OpenAI token in `.env`:
   ```env
   OPENAI_TOKEN=your_token_here
   ```
3. Ensure g++ is installed for compilation
4. Run the notebook or app

## Usage
- Enter Python code or description
- Choose optimization option and model
- Generate C++ code
- Compile and benchmark as needed

## Limitations
- Relies on LLM quality for C++ correctness and optimization
- Compilation and benchmarking require g++ and Linux/Mac environment

## Conclusion
This notebook provides a fast, modular workflow for generating, compiling, and benchmarking C++ code from Python using frontier LLMs.
