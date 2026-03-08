"""Stub knowledge base for the research assistant (topic → id, text, author, year)."""

__all__ = ["KNOWLEDGE_BASE"]

KNOWLEDGE_BASE = [
    {
        "id": "src1",
        "topic": "attention mechanisms",
        "text": "Attention mechanisms allow neural networks to dynamically focus on the most relevant parts of an input sequence when producing an output. In transformers, attention is typically implemented as scaled dot-product attention between queries, keys, and values. This enables models to capture long-range dependencies in sequences efficiently.",
        "author": "Vaswani et al.",
        "year": "2017"
    },
    {
        "id": "src2",
        "topic": "transformers",
        "text": "The Transformer architecture is a deep learning model introduced for sequence transduction tasks such as machine translation. It replaces recurrent and convolutional layers with stacked self-attention and feed-forward layers, enabling highly parallel computation and improved performance on long sequences.",
        "author": "Vaswani et al.",
        "year": "2017"
    },
    {
        "id": "src3",
        "topic": "multi-head attention",
        "text": "Multi-head attention extends the attention mechanism by running multiple attention operations in parallel. Each head learns to focus on different aspects of the input sequence, such as syntax, semantics, or positional relationships. The outputs of the heads are concatenated and projected to produce the final representation.",
        "author": "Vaswani et al.",
        "year": "2017"
    },
    {
        "id": "src4",
        "topic": "self-attention",
        "text": "Self-attention is a mechanism where each token in a sequence attends to every other token in the same sequence. This allows the model to capture contextual relationships regardless of distance, making it highly effective for tasks involving long-range dependencies in text or other sequential data.",
        "author": "Vaswani et al.",
        "year": "2017"
    },
    {
        "id": "src5",
        "topic": "positional encoding",
        "text": "Transformers lack an inherent notion of sequence order because they process tokens in parallel. Positional encodings are added to token embeddings to provide information about the relative or absolute position of tokens in the sequence. These encodings can be sinusoidal or learned during training.",
        "author": "Vaswani et al.",
        "year": "2017"
    },
    {
        "id": "src6",
        "topic": "feed-forward networks",
        "text": "Each transformer layer includes a position-wise feed-forward network applied independently to every token representation. This network typically consists of two linear transformations with a non-linear activation function such as ReLU or GELU in between.",
        "author": "Vaswani et al.",
        "year": "2017"
    },
    {
        "id": "src7",
        "topic": "layer normalization",
        "text": "Layer normalization is applied in transformer layers to stabilize and accelerate training. It normalizes activations across the feature dimension and helps maintain consistent gradient flow through deep networks.",
        "author": "Ba et al.",
        "year": "2016"
    },
    {
        "id": "src8",
        "topic": "encoder-decoder architecture",
        "text": "The original transformer model consists of an encoder and a decoder. The encoder processes the input sequence and generates contextual representations, while the decoder generates output tokens step-by-step using both self-attention and cross-attention over encoder outputs.",
        "author": "Vaswani et al.",
        "year": "2017"
    },
    {
        "id": "src9",
        "topic": "cross attention",
        "text": "Cross-attention allows the decoder in a transformer model to attend to the outputs of the encoder. This enables the decoder to use information from the input sequence while generating the target sequence.",
        "author": "Vaswani et al.",
        "year": "2017"
    },
    {
        "id": "src10",
        "topic": "large language models",
        "text": "Large Language Models (LLMs) are transformer-based neural networks trained on massive text datasets to learn statistical patterns of language. They can perform tasks such as text generation, summarization, translation, and question answering without task-specific training.",
        "author": "Various",
        "year": "2020+"
    },
]