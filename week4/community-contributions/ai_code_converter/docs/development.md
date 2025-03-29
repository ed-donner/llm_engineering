# Development Guide

This guide provides instructions for extending the CodeXchange AI application with new languages and AI models.

Before diving into development, it's recommended to review the [Architecture Diagram](./architecture_diagram.md) to understand the component relationships and application flow.

## Adding New Programming Languages

1. Update Language Configuration (`config.py`):
```python
SUPPORTED_LANGUAGES = [..., "NewLanguage"]
LANGUAGE_MAPPING = {..., "NewLanguage": "language_highlight_name"}
```

2. Add Language Detection (`core/language_detection.py`):
```python
class LanguageDetector:
    @staticmethod
    def detect_new_language(code: str) -> bool:
        patterns = [r'pattern1', r'pattern2', r'pattern3']
        return any(re.search(pattern, code) for pattern in patterns)
```

3. Add Execution Support (`core/code_execution.py`):
```python
def execute_new_language(self, code: str) -> tuple[str, Optional[bytes]]:
    with tempfile.NamedTemporaryFile(suffix='.ext', mode='w', delete=False) as f:
        f.write(code)
        file_path = f.name
    try:
        result = subprocess.run(
            ["compiler/interpreter", file_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout, None
    except Exception as e:
        return f"Error: {str(e)}", None
    finally:
        os.unlink(file_path)
```

4. Update the Dockerfile:
```dockerfile
# Add necessary dependencies for the new language
RUN apt-get update && apt-get install -y --no-install-recommends \
    new-language-package \
    && rm -rf /var/lib/apt/lists/*

# Verify the installation
RUN echo "New Language: $(new-language --version 2>/dev/null || echo 'NOT VERIFIED')"
```

5. Update the UI Components in `app.py`:
```python
def _initialize_components(self):
    # Add the new language to dropdown options
    self.source_language = gr.Dropdown(
        choices=["Python", "JavaScript", ..., "NewLanguage"],
        ...
    )
    self.target_language = gr.Dropdown(
        choices=["Python", "JavaScript", ..., "NewLanguage"],
        ...
    )
```

6. Add Language-Specific Instructions in `template.j2`:
```jinja
{% if target_language == "NewLanguage" %}
# NewLanguage-specific conversion instructions
- Follow NewLanguage best practices
- Use idiomatic NewLanguage patterns
- Handle NewLanguage-specific edge cases
{% endif %}
```

## Adding New AI Models

1. Update Model Configuration (`config.py`):
```python
NEW_MODEL = "model-name-version"
MODELS = [..., "NewModel"]
```

2. Add Model Integration (`models/ai_streaming.py`):
```python
def stream_new_model(self, prompt: str) -> Generator[str, None, None]:
    try:
        response = self.new_model_client.generate(
            prompt=prompt,
            stream=True
        )
        reply = ""
        for chunk in response:
            fragment = chunk.text
            reply += fragment
            yield reply
    except Exception as e:
        logger.error(f"New Model API error: {str(e)}", exc_info=True)
        yield f"Error with New Model API: {str(e)}"
```

3. Add API Client Initialization:
```python
def __init__(self, api_keys: dict):
    # Initialize existing clients
    ...
    
    # Initialize new model client
    if "NEW_MODEL_API_KEY" in api_keys:
        self.new_model_client = NewModelClient(
            api_key=api_keys["NEW_MODEL_API_KEY"]
        )
```

4. Update the Model Selection Logic:
```python
def stream_completion(self, model: str, prompt: str) -> Generator[str, None, None]:
    if model == "NewModel":
        yield from self.stream_new_model(prompt)
    else:
        # Existing model handling
        ...
```

## Testing

1. Add test cases for new components:
   - Unit tests for language detection
   - Integration tests for code execution
   - End-to-end tests for UI components

2. Test language detection with sample code:
   - Positive examples (valid code in the target language)
   - Negative examples (code from other languages)
   - Edge cases (minimal valid code snippets)

3. Test code execution with various examples:
   - Simple "Hello World" programs
   - Programs with external dependencies
   - Programs with different runtime characteristics
   - Error handling cases

4. Test model streaming with different prompts:
   - Short prompts
   - Long prompts
   - Edge cases (empty prompts, very complex code)
   - Error handling

5. Verify error handling and edge cases:
   - API rate limiting
   - Network failures
   - Invalid inputs
   - Resource constraints

## Logging

The application uses a structured logging system:

- JSON formatted logs with timestamps
- Stored in `logs` directory
- Separate console and file logging
- Detailed execution metrics

To add logging for new components:

```python
import logging
logger = logging.getLogger(__name__)

def new_function():
    try:
        logger.info("Starting operation", extra={"component": "new_component"})
        # Function logic
        logger.info("Operation completed", extra={"component": "new_component", "metrics": {...}})
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True, extra={"component": "new_component"})
```
