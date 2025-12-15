# LLM Tutor

An intelligent tutoring system that uses Large Language Models to provide structured, educational responses to user questions. The system employs a two-stage approach: first structuring the user's question using a meta-prompt, then generating a comprehensive educational response using system prompts and few-shot examples.

## Features

- **Two-Stage Processing**: Questions are first structured using a meta-prompt, then processed with educational context
- **Multiple Model Support**: Works with both GPT-4o-mini and Llama 3.2 models
- **Few-Shot Learning**: Uses example conversations to improve response quality
- **Streaming Support**: Real-time response generation for better user experience
- **Robust Error Handling**: Comprehensive error handling for file operations and API calls
- **Configurable Prompts**: Easy-to-modify system prompts and meta-prompts
- **Interactive Command Line**: Clean, user-friendly command-line interface

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd LLM_tutor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or using uv (recommended):
```bash
uv add openai python-dotenv frontmatter
```

3. Set up environment variables:
Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Project Structure

```
LLM_tutor/
├── llm_tutor.py              # Main command-line application
├── prompts/
│   ├── system_prompt.txt     # System prompt for educational responses
│   ├── meta_prompt.txt       # Meta-prompt for question structuring
│   └── few_shots/            # Example conversations for few-shot learning
│       └── *.md              # Markdown files with frontmatter
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project configuration
└── README.md                # This file
```

## Usage

### Command Line Interface

Run the interactive tutor from the command line:

```bash
python llm_tutor.py
```

The program will:
1. Ask you to choose between GPT-4o-mini and Llama 3.2
2. Prompt you to enter your question
3. Structure your question using the meta-prompt
4. Generate an educational response with streaming output
5. Allow for follow-up questions in the same session

### Programmatic Usage

```python
from llm_tutor import LLMTutor, get_client

# Initialize the tutor
client = get_client("openai")  # or "ollama"
tutor = LLMTutor('gpt-4o-mini', client)

# Get a structured question
question = "What is machine learning?"
structured_question = tutor.get_structured_question(question)

# Get the educational response
response = tutor.get_response(structured_question, stream=True)
print(response)
```

## Configuration

### Prompts

- **System Prompt** (`prompts/system_prompt.txt`): Defines the educational persona and response style
- **Meta Prompt** (`prompts/meta_prompt.txt`): Used to structure and clarify user questions
- **Few-Shot Examples** (`prompts/few_shots/*.md`): Example conversations with frontmatter containing user questions

### Few-Shot Examples Format

Create markdown files in `prompts/few_shots/` with the following structure:

```markdown
---
user: "What is the difference between supervised and unsupervised learning?"
---

Supervised learning uses labeled training data to learn a mapping from inputs to outputs, while unsupervised learning finds patterns in data without explicit labels. For example, supervised learning might learn to classify emails as spam or not spam using examples of each type, while unsupervised learning might group customers by purchasing behavior without knowing the "correct" groups in advance.
```

## API Requirements

- **OpenAI API Key**: Required for GPT-4o-mini model access
- **Ollama**: Required for local Llama 3.2 model access

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   # or with uv: uv add openai python-dotenv frontmatter
   ```

2. **Set up your API key**:
   Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

3. **Run the tutor**:
   ```bash
   python llm_tutor.py
   ```

4. **Follow the prompts**:
   - Choose your model (1 for OpenAI, 2 for Ollama)
   - Enter your question
   - Ask follow-up questions as needed

## Error Handling

The application includes comprehensive error handling for:
- Missing or invalid API keys
- File not found errors
- Permission errors
- Unicode decoding errors
- API request failures
- Keyboard interrupts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your OpenAI API key is correctly set in the `.env` file
2. **File Not Found**: Check that all prompt files exist in the correct directories
3. **Permission Errors**: Ensure the application has read access to all files
4. **Model Not Available**: Verify that the selected model is available in your environment

### Getting Help

If you encounter issues:
1. Check the error messages for specific guidance
2. Verify your API keys and model availability
3. Ensure all required files are present
4. Check the project structure matches the expected layout
