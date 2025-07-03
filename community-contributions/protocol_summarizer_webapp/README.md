# Protocol Summarizer Webapp

A Streamlit web application for searching and summarizing clinical trial protocols from ClinicalTrials.gov using Large Language Models. This tool enables researchers and clinical professionals to quickly extract key information from clinical trial protocols.

## Features
- Search for clinical trials by keyword
- Display a list of studies with title and NCT number
- Select a study to summarize
- Fetch the protocol's brief summary from ClinicalTrials.gov API
- Automatically summarize the protocol using OpenAI's LLM
- Extract structured information like study design, population, interventions, and endpoints

## Installation

1. Clone this repository:
   ```sh
   git clone https://github.com/albertoclemente/protocol_summarizer.git
   cd protocol_summarizer/protocol_summarizer_webapp
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

1. Run the Streamlit app:
   ```sh
   streamlit run app.py
   ```

2. In your browser:
   - Enter a disease, condition, or keyword in the search box
   - Select the number of results to display
   - Click the "Search" button
   - Select a study from the results
   - Click "Summarize Protocol" to generate a structured summary

## Technical Details

- Uses ClinicalTrials.gov API v2 to retrieve study information
- Implements fallback methods to handle API changes or failures
- Extracts protocol brief summaries using reliable JSON parsing
- Generates structured summaries using OpenAI's GPT models

## Requirements

- Python 3.7+
- Streamlit
- Requests
- OpenAI Python library
- python-dotenv

## Contribution

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License
