# Transformers and Attention

The transformer architecture, introduced in the 2017 paper "Attention Is All You Need," is the foundation of most modern language and vision models. It replaces recurrent layers with **self-attention**, allowing the model to weigh the importance of every token in the sequence when processing each position.

## Self-Attention

In self-attention, each token is mapped to a query, key, and value. The output at a position is a weighted sum of values, where weights come from the similarity (e.g., dot product) between that position’s query and all keys. This lets the model capture long-range dependencies in one step, unlike RNNs that process sequentially.

## Key Components

Transformers use **multi-head attention**: several attention "heads" run in parallel, each learning different types of relationships. They also use **positional encodings** (or embeddings) so the model knows token order. Layers typically alternate between attention and feed-forward sub-layers, with residual connections and layer normalization for stable training.

## Impact

Transformers scale well with data and compute and can be parallelized efficiently on GPUs. They underpin BERT (encoder-only), GPT (decoder-only), and T5 (encoder-decoder), and have been extended to vision (ViT), multimodal (CLIP), and other domains.
