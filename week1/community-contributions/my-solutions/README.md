# Week 1 Solutions - My Implementation

This directory contains my solutions to the Week 1 assignments without overwriting the original course content.

## Structure

```
week1/my-solutions/
├── README.md                           # This file
├── day1-solution.ipynb               # Day 1 web scraping solution
├── day2-solution.ipynb               # Day 2 solution (to be completed)
├── day4-solution.ipynb               # Day 4 solution (to be completed)
├── day5-solution.ipynb               # Day 5 solution (to be completed)
└── week1-exercise-solution.ipynb     # Week 1 exercise solution
```

## Solutions Completed

### ✅ Day 1 Solution (`day1-solution.ipynb`)
- **Features**: Web scraping with requests and BeautifulSoup
- **SSL Handling**: Fixed Windows SSL certificate issues
- **OpenAI Integration**: Website summarization using GPT-4o-mini
- **Parser**: Uses html.parser to avoid lxml dependency issues

### ✅ Week 1 Exercise Solution (`week1-exercise-solution.ipynb`)
- **Features**: Technical question answerer using both OpenAI and Ollama
- **Models**: GPT-4o-mini with streaming + Llama 3.2
- **Comparison**: Side-by-side response analysis
- **Functionality**: Can handle any technical programming question

### ✅ Day 2 Solution (`day2-solution.ipynb`)
- **Features**: Chat Completions API understanding and implementation
- **OpenAI Integration**: Multiple model testing and comparison
- **Ollama Integration**: Local model testing with Llama 3.2
- **Advanced Scraping**: Selenium fallback for JavaScript-heavy sites
- **Model Agnostic**: Works with both OpenAI and Ollama models

### ✅ Day 4 Solution (`day4-solution.ipynb`)
- **Features**: Tokenization and text processing techniques
- **Token Analysis**: Understanding tokenization with tiktoken
- **Cost Estimation**: Token counting and cost calculation
- **Text Chunking**: Smart text splitting strategies
- **Advanced Processing**: Token-aware text processing

### ✅ Day 5 Solution (`day5-solution.ipynb`)
- **Features**: Business solution - Company brochure generator
- **Intelligent Selection**: LLM-powered link selection
- **Content Aggregation**: Multi-page content collection
- **Professional Output**: Business-ready brochure generation
- **Style Options**: Professional and humorous brochure styles

## How to Use

1. **Run the solutions**: Open any `.ipynb` file and run the cells
2. **Modify questions**: Change the `question` variable in the exercise solution
3. **Test different websites**: Modify URLs in the Day 1 solution
4. **Compare models**: Use the exercise solution to compare OpenAI vs Ollama responses

## Key Features Implemented

### Day 1 Solution
- ✅ SSL certificate handling for Windows
- ✅ Web scraping with error handling
- ✅ BeautifulSoup with html.parser (no lxml dependency)
- ✅ OpenAI API integration
- ✅ Markdown display formatting
- ✅ Website content summarization

### Week 1 Exercise Solution
- ✅ OpenAI GPT-4o-mini with streaming
- ✅ Ollama Llama 3.2 integration
- ✅ Side-by-side response comparison
- ✅ Technical question answering
- ✅ Error handling for both APIs

### Day 2 Solution
- ✅ Chat Completions API understanding
- ✅ Multiple model testing and comparison
- ✅ Ollama local model integration
- ✅ Advanced web scraping with Selenium
- ✅ Model-agnostic summarization

### Day 4 Solution
- ✅ Tokenization with tiktoken library
- ✅ Token counting and cost estimation
- ✅ Text chunking strategies
- ✅ Advanced text processing
- ✅ Cost optimization techniques

### Day 5 Solution
- ✅ Intelligent link selection using LLM
- ✅ Multi-page content aggregation
- ✅ Professional brochure generation
- ✅ Business-ready output formatting
- ✅ Style options (professional/humorous)

## Notes

- All solutions are self-contained and don't modify original course files
- SSL issues are handled for Windows environments
- Both OpenAI and Ollama integrations are included
- Solutions include proper error handling and user feedback
- Code is well-documented and follows best practices

## Next Steps

1. Complete remaining day solutions (Day 2, 4, 5)
2. Test all solutions thoroughly
3. Prepare for PR submission
4. Document any additional features or improvements
