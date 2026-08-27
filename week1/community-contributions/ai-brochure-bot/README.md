# BrochureBot 🖥️📄 – AI-Powered Brochure Builder

BrochureBot is an AI-powered tool designed to help businesses, investors, and recruits create stunning brochures effortlessly. With smart templates, AI-driven content generation, and an easy-to-use interface, BrochureBot allows you to export professional brochures as PDFs or print-ready formats in seconds. Fast, simple, and professional.

## Features

- AI-Driven Content Generation: Automatically generate brochure content using advanced AI models like GPT-4 and DeepSeek.
- Flexible LLM Providers: Choose between OpenAI, Ollama (via API or library), and DeepSeek for content generation.
- Web Content Extraction: Fetch and format links from company websites to gather relevant information.
- Customizable Brochures: Create structured brochures with sections like overview, culture, customers, and career opportunities.
- Error Handling: Robust error handling for reliable performance.

## Project Structure

```
ai-brochure-bot/
│-- summarizer/
│   │-- __init__.py
│   │-- fetcher.py       # Web content fetching logic
│   │-- summarizer.py    # Main summarization logic
│   │-- brochure.py      # Brochure generation logic
│   │-- llm_handler.py   # Generic LLM handling logic
│-- utils/
│   │-- __init__.py
│   │-- config.py        # Environment configuration
│-- main.py              # Entry point of the app
│-- .env                 # Environment variables
│-- requirements.txt     # Python dependencies
│-- README.md            # Project documentation
```

## Prerequisites

- Python 3.8 or higher
- OpenAI API Key (You can obtain it from [OpenAI](https://platform.openai.com/signup))
- Ollama installed locally ([Installation Guide](https://ollama.ai))
- `conda` for managing environments (optional)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/ai-brochure-bot.git
   cd ai-brochure-bot
   ```

2. **Create a virtual environment (optional but recommended):**

   ```bash
   conda create --name ai-brochure-bot-env python=3.9
   conda activate ai-brochure-bot-env
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**

   Create a `.env` file in the project root and add your OpenAI API key (if using OpenAI):

   ```env
   OPENAI_API_KEY=your-openai-api-key
   OLLAMA_API_URL=http://127.0.0.1:11434/api/chat
   DEEPSEEK_API_KEY=your-deepseek-api-key
   ```

## Usage

1. **Run the BrochureBot:**

   ```bash
   python main.py
   ```

2. **Sample Prompts:**

   ```shell
   Enter the company name (default: "ABC").
   Enter the company website URL (default: "https://example.com").
   Choose the LLM model (default: "deepseek-r1:1.5B" or "gpt-4").
   Select the provider (default: "ollama_api").
   AI refers to machines demonstrating intelligence similar to humans and animals.
   ```

3. **Sample Output:**

   ```shell
   Enter company name: AB
   Enter company website: https://example.com
   Enter LLM model (default: deepseek-r1:1.5B, gpt-4): gpt-4
   Enter provider (openai/ollama(ollama_lib/ollama_api), default: ollama_api): openai

   Generated Brochure:

   # ABC Brochure

   ## Overview
   ABC is a leading AI company specializing in natural language processing and transformer models.

   ## Culture
   Our culture is built on collaboration, innovation, and a passion for AI.

   ## Customers
   We serve a wide range of customers, from startups to Fortune 500 companies.

   ## Career Opportunities
   Join our team and work on cutting-edge AI technologies.
   ```

## Configuration

You can modify the model, provider, and other settings in main.py:

```python
model_choice = input("Enter LLM model (default: deepseek-r1:1.5B, gpt-4): ") or "deepseek-r1:1.5B"
provider_choice = input("Enter provider (openai/ollama(ollama_lib/ollama_api), default: ollama_api): ") or "ollama_api"
```

## Error Handling

If any issues occur, the script will print an error message, for example:

```
Error: No links found. Exiting...
```

## Dependencies

The required dependencies are listed in `requirements.txt`:

```
openai
python-dotenv
requests
ollama
```

Install them using:

```bash
pip install -r requirements.txt
```

## Contributing

Contributions are welcome! Feel free to fork the repository and submit pull requests.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Contact

For any inquiries, please reach out to:

- Linkedin: https://www.linkedin.com/in/khanarafat/
- GitHub: https://github.com/raoarafat
