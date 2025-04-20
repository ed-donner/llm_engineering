# Website Summary Tool

A Python tool that generates concise summaries of websites using different Large Language Models (LLMs). This tool supports both OpenAI's API and local Llama models via Ollama.

## 1. How to Use - Use the Example code

### Start the environment
#### Start Anaconda

Go to the project folder, e.g:
```Bash
cd /Users/andresmendoza/data/mydev/_apps/ai/llm_engineer_course/llm_engineering
```

Start the environment and launch the Jupyter webapp.
```Bash
conda activate llms
jupyter lab
```

#### Start Local Llama
Open a new terminal, and from Anywhere:
```Bash
ollama run llama3.2
```

Note: to shut it down, type `/bye` from the interaction console. Or just `ctrl + C`

For more details see: [Data Science environment - Setup](https://docs.google.com/document/d/1z2Go6Eo29knpe1e35MULCuk8EISwLFNopxlzUCDcEM8/edit?usp=sharing)

### Run the sample file
With the enviroenment up and running (Llama is locally running and Jupyter Lab is on the browser), go to where the sample notebook is located:
`/Users/andresmendoza/data/mydev/_apps/ai/llm_engineer_course/llm_engineering/week1/community-contributions/website-summary/src/example_usage.ipynb`

You could launch it from:
- Jupiter Lab: Select the notebook file, and run it as shift+enter:
- Terminal: `python example_usage.ipynb`

#### Terminal

## 2. How to use it - Code a main file.
### Basic Usage

```python
from llm.llm_factory import LLMFactory
from main_summarize import summarize_url

# Create an OpenAI client
openai_client = LLMFactory.create_client("openai")

# Validate credentials
is_valid, message = openai_client.validate_credentials()
if is_valid:
    # Summarize a website
    url = "https://example.com"
    summary = summarize_url(openai_client, url)
    print(summary)
```

### Choosing an LLM Provider

You can easily switch between OpenAI and Llama:

```python
# Use OpenAI
client = LLMFactory.create_client("openai")

# Or use Llama (via Ollama)
client = LLMFactory.create_client("llama")
```

### Customizing Prompts

You can customize how the tool interacts with the LLM by modifying the system and user prompts:

```python
from llm.helper.prompt_utils import PromptManager

# Create a custom prompt manager
custom_system_prompt = "You are a tech documentation specialist. Analyze this website and provide a technical summary."
custom_user_prompt = """
You are reviewing a tech website titled {title}.
Analyze the content below and provide:
1. A brief technical summary (2-3 sentences)
2. Key technical features (max 3 bullet points)
3. Target audience

Content:
{text}
"""

# Initialize custom prompt manager
prompt_manager = PromptManager(custom_system_prompt, custom_user_prompt)

# Use custom prompts for summarization
summary = summarize_url(client, url, prompt_manager=prompt_manager)
```

#### PromptManager Parameters

The `PromptManager` class accepts the following parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `system_prompt` | str | DEFAULT_SYSTEM_PROMPT | The system prompt that sets the behavior of the AI assistant |
| `user_prompt_template` | str | DEFAULT_USER_PROMPT_TEMPLATE | The template for user messages that will be populated with website content |

The system prompt is sent as a system message to the LLM, while the user prompt template is formatted with the website's title and text before being sent as a user message.

### Advanced Options

You can pass additional parameters to the LLM when generating content:

```python
from main_summarize import summarize_url_with_options

# For OpenAI
summary = summarize_url_with_options(
    openai_client, 
    url,
    model="gpt-4o",  # Use a specific model
    temperature=0.3,  # Lower temperature for more deterministic outputs
    max_tokens=1000   # Limit response length
)

# For Llama
summary = summarize_url_with_options(
    llama_client, 
    url,
    model="llama3.2:latest",
    temperature=0.5
)
```

## 2. Setup Requirements

### Prerequisites

- Python 3.10 or higher
- Anaconda or Miniconda (recommended for environment management)
- An OpenAI API key (if using OpenAI)
- Ollama installed locally (if using Llama)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/website-summary-tool.git
   cd website-summary-tool
   ```

2. Create and activate a Conda environment:
   ```bash
   conda create -n website-summary python=3.11
   conda activate website-summary
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root:
   ```
   # OpenAI Configuration (required for OpenAI)
   OPENAI_API_KEY=sk-your-openai-api-key

   # Llama Configuration (optional, defaults to http://localhost:11434)
   LLAMA_API_URL=http://localhost:11434
   ```

### Setting Up Ollama (for Llama models)

1. Install Ollama from [ollama.ai](https://ollama.ai/)

2. Pull the Llama model:
   ```bash
   ollama pull llama3.2:latest
   ```

3. Start the Ollama server:
   ```bash
   ollama serve
   ```

You can also start Ollama programmatically from your Python code:

```python
import subprocess
import time

def start_ollama():
    """Start the Ollama server as a subprocess."""
    try:
        print("Starting Ollama server...")
        # Start Ollama as a background process
        process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for the server to start
        time.sleep(5)
        
        # Check if the process is running
        if process.poll() is None:
            print("Ollama server started successfully!")
            return process
        else:
            print("Failed to start Ollama server.")
            return None
    except Exception as e:
        print(f"Error starting Ollama server: {str(e)}")
        return None

# Usage
ollama_process = start_ollama()

# When you're done with the program
if ollama_process:
    ollama_process.terminate()
    print("Ollama server stopped.")
```

### Starting Jupyter Lab

To run the example notebook:

```bash
conda activate website-summary
cd src
jupyter lab
```

Then open `example_usage.ipynb` to experiment with the tool.

## 3. Code Structure Overview

```
website-summary/
├── src/
│   ├── example_usage.ipynb       # Example notebook demonstrating usage
│   ├── main_summarize.py         # Main functions for website summarization
│   ├── config/                   # Configuration constants
│   │   ├── __init__.py
│   │   └── constants.py
│   ├── helper/                   # Helper utilities
│   │   ├── __init__.py
│   │   ├── prompt_utils.py       # Utility for managing LLM prompts
│   │   └── web_scraper.py        # Web scraping functionality
│   ├── llm/                      # LLM integration code
│   │   ├── __init__.py
│   │   ├── base_client.py        # Abstract base class for LLM clients
│   │   ├── llm_factory.py        # Factory for creating LLM clients
│   │   ├── llama/                # Llama-specific code
│   │   │   ├── llama_client.py   # Llama client implementation
│   │   │   └── helper/
│   │   ├── open_api/             # OpenAI-specific code
│   │   │   └── openai_client.py  # OpenAI client implementation
│   │   └── helper/
│   │       └── prompt_utils.py   # Prompt utilities
│   └── structures/               # Data structures
│       ├── __init__.py
│       └── models.py             # Data models including Website class
```

### Key Components

- **LLMFactory**: Creates the appropriate LLM client based on the provider name.
- **BaseLLMClient**: Abstract base class that defines the interface for all LLM clients.
- **OpenAIClient**: Implementation of the client for the OpenAI API.
- **LlamaClient**: Implementation of the client for Llama models via Ollama.
- **PromptManager**: Manages the system and user prompts for LLM interactions.
- **WebScraper**: Extracts content from websites.
- **Website**: Data model that holds the title and text content of a website.

## Workflow Diagram

```
+----------------+      +---------------+      +------------------+
| URL Input      |----->| Web Scraper   |----->| Website Object   |
+----------------+      +---------------+      +------------------+
                                                       |
                                                       v
+----------------+      +---------------+      +------------------+
| LLM Response   |<-----| LLM Client    |<-----| Prompt Manager   |
+----------------+      +---------------+      +------------------+
```

## Example Implementation

The example notebook demonstrates how to:

1. Create LLM clients for both OpenAI and Llama
2. Validate credentials for each provider
3. Fetch and summarize website content
4. Use custom prompts for specialized summaries

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.