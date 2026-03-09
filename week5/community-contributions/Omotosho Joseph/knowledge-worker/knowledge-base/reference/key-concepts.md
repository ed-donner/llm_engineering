# Key LLM Engineering Concepts Reference

## Model Selection Strategy
When choosing an LLM, consider three axes: intelligence (accuracy on your task), cost (price per token), and speed (tokens per second). No single model wins on all three. GPT-4o is high intelligence but expensive. GPT-4o-mini is cheap and fast but less capable. Claude Sonnet balances all three well.

## The Chinchilla Scaling Law
Parameters and training data must be balanced. The optimal ratio is roughly 20 tokens per parameter. A model with 7 billion parameters should ideally be trained on 140 billion tokens. Under-training a large model wastes parameters. Over-training a small model hits diminishing returns.

## AI Benchmarks and Their Limitations
- **MMLU-Pro**: Tests broad academic knowledge across 57 subjects
- **GPQA**: Graduate-level science questions that even PhD holders find hard
- **HLE**: Humanity's Last Exam - extremely difficult questions to test frontier models
- **Limitations**: Data contamination (models memorize test data), benchmark overfitting (models optimized specifically for benchmarks), and saturation (benchmarks become too easy)

## The Business Metric Principle
Your own evaluation on your actual task beats any benchmark. For the code generator project, execution time in seconds was the business metric - unspoofable and directly relevant. Always define what success means for YOUR specific use case.

## The OpenAI-Compatible Client Pattern
Many providers (Anthropic via OpenRouter, Google, Groq) expose an API that mimics OpenAI's interface. You use the same `OpenAI` class but change the `base_url`. This means one codebase can switch between providers by changing a URL and model name.

## Temperature
Controls token selection diversity during inference. Temperature=0 means always pick the highest probability token (deterministic). Temperature=1 means tokens are selected proportional to their probability. Higher temperature = more variety but also more randomness and potential errors. For factual Q&A, use low temperature. For creative writing, use higher temperature.

## RAG (Retrieval Augmented Generation)
Instead of relying solely on the LLM's training data, RAG retrieves relevant documents and injects them into the prompt as context. This grounds the LLM's response in factual, up-to-date information. The pipeline: embed query → search vector store → retrieve top-k chunks → augment prompt → generate answer.

## Vector Embeddings
Dense numerical representations of text in high-dimensional space (typically 384-3072 dimensions). Semantically similar texts have vectors that are close together (high cosine similarity). Created by encoder models like all-MiniLM-L6-v2 (384 dims) or OpenAI's text-embedding-3-large (3072 dims).

## Chunking Strategies
Documents must be split into chunks before embedding. Key approaches:
- **Fixed-size**: Split every N characters with overlap (RecursiveCharacterTextSplitter)
- **Semantic**: Use an LLM to intelligently divide documents at natural boundaries
- Chunk size matters: too small loses context, too large dilutes relevance
- Overlap ensures information at chunk boundaries isn't lost

## Evaluation Metrics for RAG
- **MRR (Mean Reciprocal Rank)**: Where does the first relevant result appear? 1/rank averaged across queries
- **nDCG (Normalized Discounted Cumulative Gain)**: Measures ranking quality considering position
- **Keyword Coverage**: What percentage of expected keywords appear in retrieved chunks
- **LLM as Judge**: Use a powerful LLM to score answers on accuracy, completeness, and relevance
