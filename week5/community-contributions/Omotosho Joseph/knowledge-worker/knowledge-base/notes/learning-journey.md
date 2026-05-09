# My LLM Engineering Learning Journey

## Week 1-2: Foundations
I started learning LLM engineering through a Udemy course. In Week 2, I built a Technical Q&A assistant using Python with a Gradio UI. The assistant featured streaming responses and multi-model switching between GPT-4o-mini (via OpenAI), Claude (via OpenRouter), and Llama 3.2 (via Ollama). I implemented a system prompt for technical expertise and integrated a Stack Overflow search tool that demonstrated a full agentic loop.

## Week 3: Open Source Models
In Week 3, I built a Synthetic Product Review Generator on Google Colab using a T4 GPU. The project loaded multiple quantized open-source LLMs including LLaMA 3.2 3B and Qwen 2.5 3B, one at a time. It generated labeled product reviews across model × product × sentiment combinations and streamed progress in real time via Gradio yield generators. The output was downloadable JSON. I used BitsAndBytesConfig for 4-bit quantization to fit models on a free T4.

## Week 4: Code Generation and Evaluation
Week 4 had two projects. The first was a Python-to-C++/Rust Code Generator with a styled Gradio UI featuring gr.Code panels, gr.themes.Monochrome, and custom CSS from styles.py. It takes Python code, sends it to multiple LLMs via OpenAI and OpenRouter using the OpenAI-compatible client pattern, gets back optimized compiled code, then compiles and runs it using subprocess, comparing execution times as the business metric. The second project was a Docstring Generator tool using the same pattern.

## Week 5: RAG (Retrieval Augmented Generation)
In Week 5, I learned about RAG - a technique for grounding LLM responses in factual data. Key concepts include vector embeddings, chunking strategies, Chroma vector databases, retrieval pipelines, reranking, query rewriting, and evaluation metrics like MRR and nDCG. I built a Knowledge Worker that can answer questions about any document collection.
