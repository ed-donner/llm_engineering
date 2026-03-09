# Large Language Models (LLMs)

Large Language Models are AI systems trained on vast amounts of text to predict the next token (word or subword) in a sequence. By scaling up model size and data, they learn grammar, facts, and reasoning patterns that enable them to generate coherent and often helpful text.

## How They Work

LLMs are based on the **transformer** architecture. They process input text as sequences of tokens, apply self-attention to capture relationships between tokens, and output probability distributions over the next token. Training is done with objectives like next-token prediction or masked language modeling on huge corpora from the web, books, and code.

## Notable Models

Examples include GPT-4, Claude, Llama, and Mistral. These models have billions of parameters and can follow instructions, answer questions, write code, and summarize documents. Capabilities improve with scale (more parameters and more training data) and with alignment techniques such as reinforcement learning from human feedback (RLHF).

## Use Cases

LLMs power chatbots, code assistants, writing tools, and search. They can be used for zero-shot or few-shot tasks—answering without or with minimal examples—and can be fine-tuned or prompted for specific domains. Retrieval-augmented generation (RAG) combines LLMs with external knowledge bases to reduce hallucination and keep answers up to date.
