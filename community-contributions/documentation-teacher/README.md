# Technical Documentation Teacher

Transform complex technical documentation into easy-to-understand learning materials using AI!

## Overview

This project extends the Day 5 brochure generator concept from Week 1 to create a comprehensive learning system for any technical documentation. It analyzes documentation sites (like React, Python docs, FastAPI, etc.) and automatically generates:

- **Beginner-friendly teaching guides** with simple explanations and analogies
- **Key concepts** broken down for new learners
- **Practical code examples** with comments
- **Learning paths** (beginner → intermediate → advanced)
- **Practice quizzes** with 5 multiple-choice questions
- **Common pitfalls** and how to avoid them
- **Suggested projects** to practice concepts

## Files

- **doc_teacher.ipynb** - Main notebook with the complete implementation
- **doc_scraper.py** - Enhanced web scraper optimized for technical documentation

## How It Works

### 1. Link Analysis
The system uses GPT to analyze a documentation website's structure and identify the most relevant pages to learn from (prioritized as high/medium/low).

### 2. Content Extraction
It intelligently extracts main content from documentation pages, filtering out navigation, scripts, and other irrelevant elements.

### 3. Teaching Guide Generation
GPT processes the collected documentation and creates a comprehensive, engaging teaching guide tailored for beginners.

### 4. Quiz Generation
Optional: Generate 5 practice questions to test understanding of the key concepts.

## Usage

```python
# Generate a complete learning package for React hooks
package = generate_complete_learning_package(
    "React useState Hook", 
    "https://react.dev/reference/react/useState",
    max_links=2
)
```

### Streaming Output
For a better user experience with typewriter animation:

```python
stream_teaching_guide("React", "https://react.dev/reference/react", max_links=3)
```

### Generate Just a Quiz
```python
create_quiz("React Hooks", "https://react.dev/reference/react")
```

## Supported Documentation Sites

Works great with any well-structured technical documentation:
- Framework docs (React, Vue, Angular, Svelte)
- Language docs (Python, JavaScript, Rust, Go)
- Library docs (pandas, NumPy, TensorFlow, PyTorch)
- API documentation (Stripe, Twilio, AWS)
- And many more!

## Setup Requirements

1. OpenAI API key (or compatible service via OpenRouter)
2. Python libraries: `requests`, `beautifulsoup4`, `openai`, `python-dotenv`
3. `.env` file with API configuration

## Business Applications

- **Corporate Training**: Auto-generate training materials for internal tools
- **Developer Onboarding**: Create personalized learning paths for new team members
- **Educational Platforms**: Build adaptive learning content from any tech docs
- **Technical Writing**: Generate tutorial drafts from API documentation
- **Documentation Enhancement**: Create supplementary learning materials for existing docs

## Future Enhancements

- Code example validation and execution
- Interactive code playgrounds
- Video script generation
- Difficulty level customization
- Multi-language support
- Integration with learning management systems (LMS)

## Example Output

The system generates teaching guides with:
- Clear overview of the technology
- Structured key concepts with real-world analogies
- Copy-paste ready code examples
- Recommended learning order
- Common mistakes to avoid
- Practice project ideas

## Notes

This project demonstrates:
- Advanced prompt engineering with structured outputs (JSON)
- Multi-step AI workflows and orchestration
- Web scraping and content extraction
- Building educational tools with LLMs
- Streaming responses for better UX

Perfect for anyone looking to understand how to build production-ready AI applications that combine multiple API calls and external data sources!

---

Created as part of the LLM Engineering bootcamp. Enjoy! 🚀
