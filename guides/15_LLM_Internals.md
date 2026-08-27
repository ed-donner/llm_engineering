# Introduction to Internal LLM Structure

This document gives a high‑level overview of how a large language
model (LLM) is organised internally. It is intended to help a reader
get familiar with the main components and how they interact. For more
in‑depth background see the useful discussion at
https://bbycroft.net/llm.

## Core components

* **Tokenizer / vocabulary** – the first stage of any model. Input text
    is split into tokens (words, subwords, bytes) and mapped to integer
    IDs. The tokenizer defines the model’s “language”.

* **Embedding layer** – converts token IDs to dense vectors. These
    embeddings capture positional and semantic information and are the
    model’s first numerical representation of the prompt.

* **Transformer blocks** – the workhorse of modern LLMs. A stack of
    identical layers, each containing
    * multi‑head self‑attention (queries, keys, values, attention masks),
    * position‑wise feed‑forward networks,
    * residual connections and layer normalisation.
    The number of layers, width (hidden size) and number of heads
    determine the model’s capacity.

* **Positional encodings** – since transformers have no innate sense of
    order, fixed or learned positional vectors are added to embeddings to
    inject sequence information.

* **Output / projection layer** – the final hidden state of the last
    transformer block is projected back into the vocabulary space to
    produce logits over possible next tokens. A softmax converts logits
    to probabilities for sampling or greedy decoding.

## Training and inference

* **Pre‑training** – models are trained on massive corpora using
    self‑supervised objectives (e.g. causal language modelling). The
    training loop back‑propagates errors through all layers and updates
    weights.

* **Fine‑tuning** – a pre‑trained backbone may be adapted to a
    downstream task, either by full‑model fine‑tuning or techniques like
    adapters, LoRA, or prompt tuning.

* **Decoding strategies** – during inference the model generates text by
    iteratively sampling from the output distribution. Common algorithms
    include greedy search, beam search, top‑k/top‑p sampling, and
    temperature scaling.

## Memory and optimisation

* **Parameter storage** – all weights live in GPU/CPU memory; efficient
    implementations shard them across devices for large models.

* **Attention caching** – for long sequential decoding the model caches
    past keys/values to avoid recomputing them at each step.

* **Quantisation & pruning** – techniques to reduce model size and
    latency by representing weights with fewer bits or removing redundant
    parameters.

## Putting it all together

At runtime an input string passes through the tokenizer, embeddings and
positional encodings, then traverses the transformer stack. The output
logits are turned into tokens which are fed back in for autoregressive
generation. The site linked above provides diagrams and deeper analysis
of each piece; this note serves as a quick reference for understanding
the internal wiring of an LLM.