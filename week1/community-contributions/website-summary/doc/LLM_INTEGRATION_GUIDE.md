# LLM API Integration Guide

This guide explains how to use both OpenAI and Llama (via Ollama) APIs in Python applications, specifically for the Website Summary Tool.

## 1. Overview of Available LLM Clients

The application supports multiple LLM providers through a unified interface:

```python
from llm.llm_factory import LLMFactory

# Create an OpenAI client
openai_client = LLMFactory.create_client("openai")

# Create a Llama client (via Ollama)
llama_client = LLMFactory.create_client("llama")
```

Each client implements the same interface, making it easy to switch between providers.

## 2. OpenAI Integration

### 2.1 Loading the OpenAI API Key

The first step in using the OpenAI API is to load your API key:

```python
import os
from dotenv import load_dotenv

def load_api_key():
    """Load environment variables from .env file and return the API key."""
    load_dotenv(override=True)
    return os.getenv('OPENAI_API_KEY')
```

This function:
- Uses `dotenv` to load environment variables from a `.env` file
- Returns the API key from the environment variables
- The `override=True` parameter ensures that environment variables in the `.env` file take precedence

### 2.2 Initializing the OpenAI Client

Initialize the OpenAI client to make API calls:

```python
from openai import OpenAI

def initialize_openai_client():
    """Initialize the OpenAI client."""
    load_dotenv(override=True)  # Load environment variables including OPENAI_API_KEY
    return OpenAI()  # The client automatically uses OPENAI_API_KEY from environment
```

**Important Note**: The newer versions of the OpenAI Python library automatically load the API key from the environment variable `OPENAI_API_KEY`. You don't need to explicitly pass the API key when creating the client or making requests. When you call `load_dotenv(override=True)`, it loads the API key into the environment, and the OpenAI client uses it automatically.

If you want to explicitly set the API key instead of relying on environment variables, you can do:

```python
from openai import OpenAI

client = OpenAI(api_key="your-api-key-here")
```

### 2.3 Formatting Messages for OpenAI

The `OpenAIClient` implements the `format_messages` method from the `BaseLLMClient` abstract class:

```python
def format_messages(self, messages):
    """
    Format messages for OpenAI API.
    
    Args:
        messages: List of message dictionaries with role and content
        
    Returns:
        list: The messages formatted for OpenAI
    """
    # OpenAI already uses the format we're using, so we can return as-is
    return messages
```

Since our internal message format already matches what OpenAI expects, this implementation simply returns the messages unchanged.

### 2.4 Making OpenAI API Requests

Make a request to the OpenAI API:

```python
def generate_content(self, messages, model=None, **kwargs):
    """Generate content from OpenAI."""
    
    # Format messages appropriately for OpenAI
    formatted_messages = self.format_messages(messages)
    
    response = self.client.chat.completions.create(
        model=model,
        messages=formatted_messages,
        **kwargs
    )
    return response.choices[0].message.content
```

The API key is automatically used from the environment variables - you don't need to pass it in each request.

## 3. Llama Integration (via Ollama)

### 3.1 Loading Llama Configuration

Configure the connection to a local Ollama server:

```python
def _load_config(self):
    """Load Llama configuration from .env file."""
    load_dotenv(override=True)
    self.api_base = os.getenv('LLAMA_API_URL', 'http://localhost:11434')
```

The default URL for Ollama is `http://localhost:11434`, but you can customize it in your `.env` file.

### 3.2 Initializing the Llama Client

Initialize the Llama client to connect to Ollama:

```python
def initialize(self):
    """Initialize the Llama client by loading config."""
    self._load_config()
    return self
```

### 3.3 Formatting Messages for Llama

The `LlamaClient` implements the `format_messages` method to convert the standard message format to what Ollama expects:

```python
def format_messages(self, messages):
    """
    Format messages for Ollama API.
    
    Args:
        messages: List of message dictionaries with role and content
        
    Returns:
        str: The messages formatted as a prompt string for Ollama
    """
    return self._convert_messages_to_prompt(messages)
```

The actual conversion is done by the `_convert_messages_to_prompt` method:

```python
def _convert_messages_to_prompt(self, messages):
    """Convert standard messages to Ollama prompt format."""
    prompt = ""
    for msg in messages:
        role = msg.get("role", "").lower()
        content = msg.get("content", "")
        
        if role == "system":
            prompt += f"<system>\n{content}\n</system>\n\n"
        elif role == "user":
            prompt += f"User: {content}\n\n"
        elif role == "assistant":
            prompt += f"Assistant: {content}\n\n"
        else:
            prompt += f"{content}\n\n"
            
    # Add final prompt for assistant response
    prompt += "Assistant: "
    return prompt
```

### 3.4 Making Llama API Requests

Make a request to the Llama API via Ollama:

```python
def generate_content(self, messages, model=None, **kwargs):
    """Generate content from Llama."""
    
    # Convert messages to Ollama format
    prompt = self.format_messages(messages)
    
    payload = {
        "model": model or self.default_model,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(
            f"{self.api_base}/api/generate",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json().get("response", "")
```

## 4. Creating Message Structure

To interact with either API, you need to structure your messages in a specific format:

```python
def create_user_prompt(self, website):
    return self.user_prompt_template.format(title=website.title, text=website.text)

def create_messages(self, website):
    return [
        {"role": "system", "content": self.system_prompt},
        {"role": "user", "content": self.create_user_prompt(website)}
    ]
```

System and user prompt examples:
```python
DEFAULT_SYSTEM_PROMPT = ("You are an assistant that analyzes the contents of a website "
             "and provides a short summary, ignoring text that might be navigation related. "
             "Respond in markdown.")

DEFAULT_USER_PROMPT_TEMPLATE = """
You are looking at a website titled {title}
The contents of this website is as follows; 
please provide a short summary of this website in markdown.
If it includes news or announcements, then summarize these too.

{text}
"""
```

This format includes:
- A system message that sets the behavior of the AI assistant
- A user message containing the actual content to process
- The website object is used to insert relevant content into the user prompt template

## 5. Complete Integration Flow

Here's the complete flow for integrating with either LLM API:

```python
# Create the appropriate client
client = LLMFactory.create_client("openai")  # or "llama"

# Validate credentials
is_valid, message = client.validate_credentials()
if not is_valid:
    print(message)
    exit(1)

# Optional: Test connectivity
test_response = client.test_connection("Hello, this is a test message.")
print("Test API response:", test_response)

# Create a prompt manager (or use default)
prompt_manager = PromptManager()  # Customize if needed

# Prepare website content
website = fetch_website_content(url)

# Generate summary with the LLM API
summary = client.generate_content(
    prompt_manager.create_messages(website),
    model=None,  # Uses default model for the client
    temperature=0.7  # Optional parameter
)
```

## A Key Note On The Abstract Interface

The system now uses an abstract base class (`BaseLLMClient`) that defines the common interface for all LLM clients. Each provider-specific client implements this interface, including the format_messages method that handles converting the standard message format to the provider's expected format.

This approach eliminates the need to first create messages in OpenAI format and then translate them. Instead, each client knows how to format messages appropriately for its specific provider.

## 6. Additional API Parameters

### OpenAI Parameters
```python
response = client.generate_content(
    messages=messages,
    model="gpt-4o-mini",
    temperature=0.7,  # Controls randomness (0-1)
    max_tokens=1500,  # Maximum length of response
    frequency_penalty=0.0,  # Reduces repetition of token sequences
    presence_penalty=0.0,  # Reduces talking about the same topics
    stop=None  # Sequences where the API will stop generating
)
```

### Llama/Ollama Parameters
```python
response = client.generate_content(
    messages=messages,
    model="llama3.2:latest",
    temperature=0.7,  # Controls randomness (0-1)
    # Other parameters supported by Ollama
)
```

## 7. Example Usage

Here's an example using both providers:

```python
# Example with OpenAI
openai_client = LLMFactory.create_client("openai")
is_valid, message = openai_client.validate_credentials()

if is_valid:
    print("OpenAI credentials validated successfully")
    url_to_summarize = "https://example.com"
    print(f"Fetching and summarizing content from {url_to_summarize}")
    summary = summarize_url(openai_client, url_to_summarize)
    print("Summary from OpenAI:", summary)

# Example with Llama
llama_client = LLMFactory.create_client("llama")
is_valid, message = llama_client.validate_credentials()

if is_valid:
    print("Llama credentials validated successfully")
    url_to_summarize = "https://example.com"
    print(f"Fetching and summarizing content from {url_to_summarize}")
    summary = summarize_url(llama_client, url_to_summarize)
    print("Summary from Llama:", summary)
```

## 8. Environment Setup

Create a `.env` file in your project root with:

```
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key

# Llama Configuration (optional, defaults to http://localhost:11434)
LLAMA_API_URL=http://localhost:11434
```

Make sure to install Ollama locally if you want to use Llama models: [Ollama Installation Guide](https://github.com/ollama/ollama)


# Annex: OpenAI vs Llama Side-by-Side Comparison

This annex provides a clear comparison between OpenAI and Llama (via Ollama) implementations for each critical step in the integration process.

## 1. Import Statements

**OpenAI:**
```python
import os
from dotenv import load_dotenv
from openai import OpenAI
```

**Llama (Ollama):**
```python
import os
import requests
from dotenv import load_dotenv
```

## 2. Client Initialization

**OpenAI:**
```python
# Load environment variables
load_dotenv(override=True)

# Initialize client (automatically uses OPENAI_API_KEY from environment)
client = OpenAI()

# Alternative with explicit API key
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)
```

**Llama (Ollama):**
```python
# Load environment variables
load_dotenv(override=True)

# Get base URL (defaults to localhost if not specified)
api_base = os.getenv('LLAMA_API_URL', 'http://localhost:11434')

# No client object is created - direct API calls are made via requests
```

## 3. Message Formatting

**OpenAI:**
```python
# The BaseLLMClient abstract method implemented for OpenAI
def format_messages(self, messages):
    """
    Format messages for OpenAI API.
    
    Args:
        messages: List of message dictionaries with role and content
        
    Returns:
        list: The messages formatted for OpenAI
    """
    # OpenAI already uses the format we're using, so we can return as-is
    return messages
```

Examples:
```python
# OpenAI uses a structured format with role-based messages
messages = [
    {"role": "system", "content": "You are an assistant that analyzes websites."},
    {"role": "user", "content": f"Summarize this website: {website_content}"}
]

# Simple concrete example: 
messages = [ 
{"role": "system", "content": "You are a helpful assistant."}, 
{"role": "user","content": "What is machine learning?"}, 
{"role": "assistant", "content": "Machine learning is a branch of artificial intelligence that focuses on building systems that learn from data."}, 
{"role": "user", "content": "Can you give me a simple example?"} 
]

```

**Llama (Ollama):**
```python
# The BaseLLMClient abstract method implemented for Llama
def format_messages(self, messages):
    """
    Format messages for Ollama API.
    
    Args:
        messages: List of message dictionaries with role and content
        
    Returns:
        str: The messages formatted as a prompt string for Ollama
    """
    return self._convert_messages_to_prompt(messages)

def _convert_messages_to_prompt(self, messages):
    """Convert standard messages to Ollama prompt format."""
    prompt = ""
    for msg in messages:
        role = msg.get("role", "").lower()
        content = msg.get("content", "")
        
        if role == "system":
            prompt += f"<system>\n{content}\n</system>\n\n"
        elif role == "user":
            prompt += f"User: {content}\n\n"
        elif role == "assistant":
            prompt += f"Assistant: {content}\n\n"
        else:
            prompt += f"{content}\n\n"
            
    # Add final prompt for assistant response
    prompt += "Assistant: "
    return prompt
```

Examples:
```python
# Simple concrete example of converted messages: # Starting with the same OpenAI-style messages messages = [ 
{"role":"system", "content": "You are a helpful assistant."}, 
{"role": "user", "content": "What is machine learning?"}, 
{"role":"assistant", "content": "Machine learning is a branch of artificial intelligence that focuses on building systems that learn from data."}, 
{"role": "user", "content": "Can you give me a simple example?"} 
]

# Convert OpenAI-style messages to Ollama format
prompt = convert_messages_to_prompt(messages)

# After conversion, the prompt would look like: 
converted_prompt = """<system> You are a helpful assistant. </system>
User: What is machine learning?

# Convert OpenAI-style messages to Ollama format
prompt = convert_messages_to_prompt(messages)
```

## 4. Making Requests

**OpenAI:**
```python
def generate_content(self, messages, model=None, **kwargs):
    """Generate content from OpenAI."""
    
    # Format messages appropriately for OpenAI
    formatted_messages = self.format_messages(messages)
    
    response = self.client.chat.completions.create(
        model=model or self.default_model,
        messages=formatted_messages,
        **kwargs
    )
    return response.choices[0].message.content
```

**Llama (Ollama):**
```python
def generate_content(self, messages, model=None, **kwargs):
    """Generate content from Llama."""
    
    # Format messages appropriately for Llama/Ollama
    prompt = self.format_messages(messages)
    
    payload = {
        "model": model or self.default_model,
        "prompt": prompt,
        "stream": False,
        **kwargs
    }

    response = requests.post(
        f"{self.api_base}/api/generate",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=60
    )
        
    if response.status_code == 200:
        return response.json().get("response", "")
```

## 5. Processing Response

**OpenAI:**
```python
# Response structure
"""
{
  "id": "chatcmpl-123abc",
  "object": "chat.completion",
  "created": 1677858242,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "This website is about..."
      },
      "index": 0,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 13,
    "completion_tokens": 7,
    "total_tokens": 20
  }
}
"""

# Extracting content
content = response.choices[0].message.content
```

**Llama (Ollama):**
```python
# Response structure (if response.status_code == 200)
"""
{
  "model": "llama3",
  "response": "This website is about...",
  "done": true
}
"""

# Extracting content
if response.status_code == 200:
    content = response.json().get("response", "")
else:
    content = f"Error: {response.status_code}, {response.text}"
```

## 6. Complete Side-by-Side Example With New Architecture

**OpenAI:**
```python
import os
from dotenv import load_dotenv
from openai import OpenAI
from llm.base_client import BaseLLMClient

class OpenAIClient(BaseLLMClient):
    def __init__(self):
        self.client = None
        self.default_model = "gpt-4o-mini"
    
    def initialize(self):
        load_dotenv(override=True)
        self.client = OpenAI()  # Uses OPENAI_API_KEY from environment
        return self
    
    def format_messages(self, messages):
        # OpenAI already uses our format, so return as-is
        return messages
    
    def generate_content(self, messages, model=None, **kwargs):
        formatted_messages = self.format_messages(messages)
        response = self.client.chat.completions.create(
            model=model or self.default_model,
            messages=formatted_messages,
            **kwargs
        )
        return response.choices[0].message.content
```

**Llama (Ollama):**
```python
import os
import requests
from dotenv import load_dotenv
from llm.base_client import BaseLLMClient

class LlamaClient(BaseLLMClient):
    def __init__(self):
        self.api_base = None
        self.default_model = "llama3"
    
    def initialize(self):
        load_dotenv(override=True)
        self.api_base = os.getenv('LLAMA_API_URL', 'http://localhost:11434')
        return self
    
    def format_messages(self, messages):
        # Convert standard message format to Ollama prompt
        return self._convert_messages_to_prompt(messages)
    
    def _convert_messages_to_prompt(self, messages):
        prompt = ""
        for msg in messages:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")
            
            if role == "system":
                prompt += f"<system>\n{content}\n</system>\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
            else:
                prompt += f"{content}\n\n"
                
        prompt += "Assistant: "
        return prompt
    
    def generate_content(self, messages, model=None, **kwargs):
        prompt = self.format_messages(messages)
        
        payload = {
            "model": model or self.default_model,
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(
            f"{self.api_base}/api/generate",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            return f"Error: {response.status_code}, {response.text}"
```

## 7. Key Differences Summary

| Aspect | OpenAI | Llama (Ollama) |
|--------|--------|----------------|
| **Authentication** | API key in environment or explicitly passed | No authentication, just URL to local server |
| **Client Library** | Official Python SDK | Standard HTTP requests |
| **Message Format Implementation** | Returns standard messages as-is | Converts to text-based prompt format |
| **Format Method Return Type** | List of dictionaries | String |
| **Request Format** | Client method calls | Direct HTTP POST requests |
| **Response Format** | Structured object with choices | Simple JSON with response field |
| **Streaming** | Supported via stream parameter | Supported via stream parameter |
| **Error Handling** | SDK throws exceptions | Need to check HTTP status codes |

## 8. The Abstract Base Class

```python
from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def initialize(self):
        """Initialize the LLM client."""
        pass
    
    @abstractmethod
    def validate_credentials(self):
        """
        Validate API credentials.
        
        Returns:
            tuple: (is_valid, message)
        """
        pass
    
    @abstractmethod
    def format_messages(self, messages):
        """
        Format messages according to the provider's requirements.
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            The properly formatted messages for this specific provider
        """
        pass
    
    @abstractmethod
    def generate_content(self, messages, model=None, **kwargs):
        """
        Generate content from the LLM.
        
        Args:
            messages: The messages to send
            model: The model to use for generation
            **kwargs: Additional provider-specific parameters
            
        Returns:
            str: The generated content
        """
        pass
```

This abstract base class ensures that all LLM clients implement the same interface, making it easy to switch between providers. The `format_messages` method is a key part of this architecture, as it allows each client to format messages appropriately for its specific provider.