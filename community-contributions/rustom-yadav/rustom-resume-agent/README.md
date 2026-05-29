# Resume Builder Agent

A conversational AI agent that guides users through structured questions to create professional HTML resumes.

## Note - when your final_resume.html is generated, you will need to format the file because all code is written in one line. You can use an online HTML formatter or a code editor with formatting capabilities to make it readable.

## How It Works

The agent:

1. Asks 7 sequential questions to collect resume information
2. Updates an HTML resume template with the provided data
3. Generates a final `final_resume.html` file with the completed resume

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file:

```env
BASE_URL=http://localhost:11434/v1
API_KEY=ollama
MODEL_NAME=llama3.2:latest
```

3. Place your `resume_template.html` template in the same directory

4. Run the script:

```bash
python resume-builder-agent.py
```

## Customization

- **Change the AI Model**: Update `MODEL_NAME` in `.env` to use any OpenAI SDK-compatible model (OpenAI, Ollama, Azure, etc.)
- **Customize the Resume**: Edit `resume_template.html` to change the resume template structure and styling

## Supported APIs

Works with any OpenAI SDK-compatible API:

- Ollama (local)
- Groq api and models
- OpenAI
- Azure OpenAI
- Any other compatible provider

Rustom Yadav - [GitHub](https://github.com/rustom-yadav)
