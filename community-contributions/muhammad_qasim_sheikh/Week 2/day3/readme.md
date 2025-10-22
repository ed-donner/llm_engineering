# AI Business Assistant

## Project Overview

This project is a prototype of an **AI-powered business consultant chatbot** built with **Gradio** and **OpenAI**. The assistant, named **Nova**, is designed to act as a virtual sales and solutions consultant for a company offering AI services such as chatbots, voice assistants, dashboards, and automation tools.

The purpose of the project is to demonstrate how an LLM (Large Language Model) can be adapted for a business context by carefully designing the **system prompt** and providing **dynamic behavior** based on user inputs. The chatbot responds to user queries in real time with streaming responses, making it interactive and natural to use.


## What’s Happening in the Code

1. **Environment Setup**  
   - The code loads the OpenAI API key from a `.env` file.  
   - The `OpenAI` client is initialized for communication with the language model.  
   - The chosen model is `gpt-4o-mini`.

2. **System Prompt for Business Context**  
   - The assistant is given a clear identity: *Nova, an AI Sales & Solutions Consultant for Reallytics.ai*.  
   - The system prompt defines Nova’s tone (professional, insightful) and role (understand user needs, propose relevant AI solutions, share examples).

3. **Dynamic Chat Function**  
   - The `chat()` function processes user input and the conversation history.  
   - It modifies the system prompt dynamically:
     - If the user mentions **price**, Nova explains pricing ranges and factors.  
     - If the user mentions **integration**, Nova reassures the user about system compatibility.  
   - Messages are formatted for the OpenAI API, combining system, history, and user inputs.  
   - Responses are streamed back chunk by chunk, so users see the assistant typing in real time.

4. **Gradio Chat Interface**  
   - A Gradio interface is created with `ChatInterface` in `messages` mode.  
   - This automatically provides a chat-style UI with user/assistant message bubbles and a send button.  
   - The title and description help set context for end users: *“Ask about automation, chatbots, dashboards, or voice AI.”*


## Key Features
- **Business-specific persona:** The assistant is contextualized as a sales consultant rather than a generic chatbot.  
- **Adaptive responses:** System prompt is adjusted based on keywords like "price" and "integration".  
- **Streaming output:** Responses are displayed incrementally, improving user experience.  
- **Clean chat UI:** Built with Gradio’s `ChatInterface` for simplicity and usability.


This project demonstrates how to combine **system prompts**, **dynamic context handling**, and **Gradio chat interfaces** to build a specialized AI assistant tailored for business use cases.
