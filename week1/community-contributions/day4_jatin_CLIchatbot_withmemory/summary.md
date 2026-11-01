# Day 4 - Building a Local AI Chatbot with Memory using Ollama

## Objective

The goal of this mini assignment was to understand how Large Language Models (LLMs) can be accessed locally through Ollama and how conversational memory works in AI chat applications.

## Technologies Used

* Python
* Ollama
* OpenAI Python SDK
* Llama 3.2 (Local Model)

## Initial Implementation

The chatbot was initially implemented using the OpenAI-compatible API exposed by Ollama:

```python
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)
```

The chatbot accepted user input and generated responses using a locally hosted LLM. However, each request was sent independently, meaning the model only received the current user message and had no knowledge of previous interactions.

As a result, the chatbot could not answer questions that relied on earlier context, such as remembering the user's name.

## Introducing Conversational Memory

To solve this limitation, a conversation history list was introduced:

```python
conversation = [
    {
        "role": "system",
        "content": "You are a helpful AI assistant."
    }
]
```
Instead of sending only the latest prompt, the entire conversation history was sent to the model:

```python
response = client.chat.completions.create(
    model="llama3.2",
    messages=conversation
)
```

This allowed the model to see previous interactions and respond based on the accumulated context.

## Debugging and Model Comparison

The first model tested was DeepSeek-R1:1.5B. Although the memory implementation was functioning correctly, the model frequently produced inconsistent and unrelated responses. This highlighted an important lesson in AI engineering:

> Memory systems can provide context, but the model must still be capable of reasoning over that context effectively.

The model was then replaced with Llama 3.2:

```python
model="llama3.2"
```

The results improved significantly, demonstrating the impact of model quality on conversational performance.

## Key Learning Outcomes

1. Learned how Ollama exposes local LLMs through an OpenAI-compatible API.
2. Understood how chat completion endpoints work.
3. Built a terminal-based AI chatbot in Python.
4. Implemented conversational memory using message history.
5. Learned that LLMs do not automatically remember previous API requests.
6. Understood that memory is typically managed by the application layer.
7. Observed how different models handle the same context differently.
8. Gained practical insight into one of the core mechanisms used by modern AI assistants such as ChatGPT, Gemini, Claude, and DeepSeek.

## Conclusion

This exercise demonstrated that conversational AI is not solely dependent on the model itself. The application is responsible for storing and supplying previous messages, while the model uses that context to generate responses. By implementing a conversation history and testing different local models through Ollama, a functional chatbot with memory was successfully created and evaluated.