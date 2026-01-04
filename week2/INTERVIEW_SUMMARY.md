# Week 2: Multi-Model API Integration & Gradio UI

## Core Concepts Covered

### 1. **Multi-Provider API Integration**
- **OpenAI API**: GPT-3.5-turbo, GPT-4o-mini, GPT-4o models
- **Anthropic API**: Claude-3-5-Sonnet with streaming support
- **Google Gemini API**: Alternative model integration
- **DeepSeek API**: Additional model provider option
- **API Key Management**: Environment variables for multiple providers

### 2. **Advanced Prompting Techniques**
- **Temperature Control**: Creativity vs consistency (0.0-1.0)
- **Max Tokens**: Response length control
- **System vs User Messages**: Role-based prompting
- **Streaming Responses**: Real-time output display
- **Model Comparison**: Testing different models on same prompts

### 3. **Gradio UI Development**
- **Gradio Framework**: Simple web UI creation
- **Interface Components**: Text inputs, dropdowns, outputs
- **Model Selection**: Dynamic model switching
- **Real-time Updates**: Live response streaming
- **User Experience**: Clean, intuitive interfaces

### 4. **Conversational AI Patterns**
- **Multi-turn Conversations**: Maintaining context
- **Model Debates**: Having different models discuss topics
- **Adversarial Conversations**: Models arguing different viewpoints
- **Conversation Management**: State handling and context preservation

### 5. **Tool Integration (Days 4-5)**
- **Function Calling**: LLMs calling external functions
- **Tool Definitions**: Structured tool schemas
- **Multiple Tools**: Handling multiple tool calls per message
- **Real-world Applications**: Flight booking, translation, etc.

## Key Code Patterns

### Multi-Model API Calls
```python
# OpenAI
response = openai.chat.completions.create(
    model='gpt-4o-mini',
    messages=messages,
    temperature=0.5
)

# Anthropic with streaming
result = claude.messages.stream(
    model="claude-3-5-sonnet-latest",
    max_tokens=200,
    temperature=0.7,
    system=system_message,
    messages=[{"role": "user", "content": user_prompt}]
)
```

### Gradio Interface
```python
import gradio as gr

def chat_with_model(message, model_choice):
    if model_choice == "GPT-4o":
        return call_gpt(message)
    elif model_choice == "Claude":
        return call_claude(message)
    # ... other models

interface = gr.Interface(
    fn=chat_with_model,
    inputs=[
        gr.Textbox(label="Your message"),
        gr.Dropdown(choices=["GPT-4o", "Claude", "Gemini"])
    ],
    outputs=gr.Textbox(label="Response")
)
```

### Function Calling
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "book_flight",
            "description": "Book a flight",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "date": {"type": "string"}
                }
            }
        }
    }
]

response = openai.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)
```

### Streaming Implementation
```python
def stream_response(prompt, model):
    stream = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    
    response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            response += chunk.choices[0].delta.content
            yield response
```

## Interview-Ready Talking Points

1. **"I built a multi-model conversational AI system with a clean web interface"**
   - Explain the benefits of supporting multiple LLM providers
   - Discuss the importance of user experience in AI applications

2. **"I implemented advanced prompting techniques and streaming responses"**
   - Show understanding of temperature, tokens, and response control
   - Demonstrate real-time user experience improvements

3. **"I integrated function calling for real-world applications"**
   - Explain how LLMs can interact with external systems
   - Discuss the practical applications of tool integration

4. **"I created a production-ready UI with Gradio"**
   - Show understanding of web UI development for AI
   - Discuss the balance between functionality and simplicity

## Technical Skills Demonstrated

- **Multi-API Integration**: OpenAI, Anthropic, Google, DeepSeek
- **UI Development**: Gradio framework, component design
- **Streaming**: Real-time response handling
- **Function Calling**: Tool integration and external API calls
- **Conversation Management**: Context handling and state management
- **Model Comparison**: Testing and evaluating different models
- **Error Handling**: Robust API error management

## Common Interview Questions & Answers

**Q: "How do you choose between different LLM providers?"**
A: "I consider factors like cost, speed, quality, and specific capabilities. For example, Claude might be better for long-form content, while GPT-4o might excel at code generation. I built a system that allows easy switching between providers."

**Q: "How do you handle API rate limits and costs?"**
A: "I implement proper error handling, use appropriate models for the task (gpt-4o-mini for simple tasks), and add caching mechanisms. I also monitor usage and implement fallback strategies."

**Q: "What's the benefit of streaming responses?"**
A: "Streaming improves user experience by providing immediate feedback, especially for long responses. It makes the AI feel more responsive and engaging, similar to how humans communicate."

**Q: "How do you ensure conversation context is maintained?"**
A: "I maintain conversation history in the messages array, implement proper context window management, and use system prompts to establish consistent behavior across the conversation."