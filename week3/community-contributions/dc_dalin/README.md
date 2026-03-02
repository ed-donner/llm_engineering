# Prompt Testing Playground

An interactive tool for testing, comparing, and visualizing LLM prompts across multiple models with detailed token-level analysis.

## Overview

The **Prompt Testing Playground** is an educational and practical tool that extends Week 3's `visualizer.py` concept, providing deep insights into how Large Language Models generate text token by token. It's designed for prompt engineers, researchers, and anyone curious about understanding LLM behavior.

## Features

### 🔍 Single Prompt Analysis
- **Token-by-Token Visualization**: See how the model predicts each token with probability heatmaps
- **Alternative Path Explorer**: View what other tokens the model considered at each position
- **Detailed Metrics**: Confidence scores, perplexity, entropy, and uncertainty measures
- **Interactive Controls**: Adjust temperature, max tokens, and model selection

### 📊 Multi-Prompt Comparison
- **Side-by-Side Testing**: Compare different prompt phrasings using the same model
- **Metrics Dashboard**: Visual comparison of confidence, perplexity, and entropy
- **Identify Best Prompts**: Quickly see which prompt variation performs better

### 🤖 Multi-Model Comparison
- **Cross-Model Testing**: Run the same prompt across GPT-4o-mini, GPT-4.1-mini, GPT-3.5-turbo, and GPT-4o
- **Performance Benchmarking**: Compare speed, quality, and token confidence across models
- **Cost-Benefit Analysis**: Understand trade-offs between different model choices

### 📈 Visualization Components
- **Probability Heatmaps**: Color-coded visualization of token confidence over time
- **Alternative Tokens Bar Charts**: See the top alternative tokens at any position
- **Metrics Comparison Charts**: Side-by-side bar charts for comparing multiple results
- **Interactive Gradio Interface**: User-friendly web UI with real-time updates

## Metrics Explained

### Average Confidence
The mean probability of all selected tokens. Higher values indicate the model is more certain about its predictions.
- **High (>0.8)**: Model is very confident
- **Medium (0.5-0.8)**: Moderate confidence
- **Low (<0.5)**: Model is uncertain

### Perplexity
Measures how "surprised" the model is by its own predictions. **Lower is better**.
- **Low (<5)**: Text is predictable and coherent
- **Medium (5-20)**: Normal variation
- **High (>20)**: Model is struggling or generating creative content

### Entropy
Measures uncertainty in the model's token predictions. Higher entropy means more alternative tokens had similar probabilities.
- **Low**: Deterministic, focused predictions
- **High**: Many alternatives were considered

### Low Confidence Tokens
Count and percentage of tokens where probability < 50%. These indicate points where the model was uncertain.

## Installation & Setup

### Prerequisites
- Python 3.8+
- OpenAI API key
- Jupyter Notebook or Google Colab

### Quick Start

1. **Clone the repository** (if not already done):
   ```bash
   cd /Users/dc_dalin/Projects/llm_engineering/week3/community-contributions/dc_dalin
   ```

2. **Ensure your `.env` file exists** in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

3. **Install dependencies** (if needed):
   ```bash
   pip install openai python-dotenv gradio matplotlib networkx pandas numpy
   ```

4. **Open the notebook**:
   ```bash
   jupyter notebook prompt_testing_playground.ipynb
   ```

5. **Run all cells** and interact with the Gradio interface!

## Usage Examples

### Example 1: Optimize a Prompt
Test different phrasings to find the most effective prompt:

```python
prompts = [
    "Explain quantum computing",
    "Explain quantum computing in simple terms",
    "Explain quantum computing to a 5-year-old"
]
results = compare_prompts(prompts, model="gpt-4o-mini")
```

Look for:
- Which prompt has highest average confidence?
- Which has lowest perplexity (better coherence)?
- Which generates the most appropriate response?

### Example 2: Choose the Right Model
Compare models for your specific use case:

```python
models = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4o"]
results = compare_models("Write a creative story opening", models)
```

Consider:
- **gpt-4o-mini**: Fastest, lowest cost, good for simple tasks
- **gpt-4.1-mini**: Better reasoning, slightly slower
- **gpt-4o**: Best quality, highest cost and latency

### Example 3: Understand Token Predictions
Analyze exactly how the model generates text:

```python
predictor = TokenPredictor("gpt-4o-mini")
result = predictor.predict_tokens("In one sentence, describe...")

# Check metrics
print(f"Average Confidence: {result['metrics']['avg_confidence']}")
print(f"Perplexity: {result['metrics']['perplexity']}")
print(f"Low Confidence Tokens: {result['metrics']['low_confidence_tokens']}")

# Visualize
fig = create_probability_heatmap(result)
plt.show()
```

## Interactive Gradio Interface

The notebook includes a comprehensive Gradio web interface with three tabs:

### 🔍 Analyze Prompt Tab
- Enter a single prompt
- Select model and parameters
- View probability heatmap and alternative tokens
- See detailed metrics

### 📊 Compare Prompts Tab
- Enter two different prompts
- Compare using the same model
- View side-by-side metrics
- Identify which prompt performs better

### 🤖 Compare Models Tab
- Enter one prompt
- Select two models to compare
- See how different models handle the same prompt
- Compare performance metrics

## Use Cases

### 1. Prompt Engineering
- Test variations of system prompts
- Optimize instruction clarity
- Find the most effective phrasing
- Reduce ambiguity in prompts

### 2. Model Selection
- Choose the right model for your task
- Balance cost vs. quality
- Understand model-specific behaviors
- Benchmark performance

### 3. Educational
- Learn how LLMs predict tokens
- Understand temperature effects
- Visualize probability distributions
- Explore alternative generation paths

### 4. Quality Assurance
- Identify low-confidence outputs
- Detect potential hallucinations
- Verify response consistency
- Monitor model behavior

### 5. Research
- Study token-level predictions
- Analyze model uncertainty
- Compare model architectures
- Export data for further analysis

## Technical Details

### Token Prediction Process
1. **Streaming API**: Uses OpenAI's streaming API to capture token-by-token generation
2. **Logprobs**: Requests log probabilities for top 5 alternative tokens at each position
3. **Metrics Calculation**: Computes confidence, perplexity, and entropy from logprobs
4. **Visualization**: Generates matplotlib plots showing probabilities and alternatives

### Metrics Formulas

**Perplexity**:
```python
perplexity = exp(-mean(logprobs))
```

**Entropy** (per token):
```python
entropy = -sum(p * log2(p)) for all token probabilities
```

**Average Confidence**:
```python
avg_confidence = mean(probabilities)
```

## Tips & Best Practices

### Temperature Settings
- **0.0-0.3**: Deterministic, focused (good for factual tasks)
- **0.5-0.7**: Balanced (default, good for most tasks)
- **0.8-1.0**: Creative, diverse (good for brainstorming)

### Interpreting Results
- **High confidence + Low perplexity** = Strong, coherent response
- **Low confidence + High perplexity** = Model is struggling
- **High entropy** = Model considered many alternatives (creative task)
- **Low entropy** = Focused, deterministic output

### Prompt Optimization
1. Start with multiple variations
2. Compare metrics across variations
3. Select the prompt with:
   - Highest average confidence
   - Lowest perplexity
   - Most appropriate output
4. Iterate and refine

## Project Structure

```
dc_dalin/
├── prompt_testing_playground.ipynb  # Main interactive notebook
└── README.md                        # This file
```

## Future Enhancements

Potential additions for future versions:
- [ ] Support for more models (Claude, Llama, etc.)
- [ ] Batch prompt testing with CSV import
- [ ] A/B testing framework
- [ ] Cost estimation per prompt/model
- [ ] Token path visualization with NetworkX graphs
- [ ] Export to PDF reports
- [ ] Integration with LangSmith/LangChain
- [ ] Prompt template library
- [ ] Historical comparison tracking

## Inspiration & Credits

This project is inspired by:
- **Week 3 visualizer.py**: The original token prediction visualizer
- **LLM Engineering Course**: Prompt engineering and model comparison concepts
- **OpenAI Logprobs API**: Makes token-level analysis possible

## Contributing

Feel free to:
- Suggest new features
- Report bugs
- Share interesting findings
- Contribute visualizations
- Add example prompts

## License

This project is part of the LLM Engineering course community contributions and follows the course's guidelines.

---

**Week 3 Contribution by dc_dalin**

*Making prompt engineering more transparent, one token at a time.*
