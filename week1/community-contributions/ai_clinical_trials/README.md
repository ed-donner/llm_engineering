AI Clinical Trials Landscape Analyzer
A Python tool that pulls real clinical trial data from ClinicalTrials.gov and uses OpenAI’s GPT-4o-mini to generate strategic healthcare research insights.
What It Does
Retrieves live clinical trial data using the official ClinicalTrials.gov API
Extracts structured fields like phase, sponsor, status, and summary
Computes quick landscape metrics (phase distribution, sponsor patterns)
Uses AI to generate a strategic brief highlighting research trends and future healthcare signals
Quick Start
Prerequisites
Python 3.8+
OpenAI API key (Get one here)
Installation
Install required packages:
pip install requests openai python-dotenv
Set up your API key
Create a .env file in the same directory:
OPENAI_API_KEY=your_openai_api_key_here
Run the notebook or script
If using a notebook:
Open in Cursor or Jupyter
Run cells in order
If using a script:
python your_script_name.py
How to Use
Basic Usage
Change the healthcare topic you want to analyze:
condition = "diabetes"
page_size = 20
Examples you can try:
condition = "breast cancer"
condition = "heart failure"
condition = "obesity"
condition = "Alzheimer"
The system will:
Pull recent trials for that condition
Compute structured metrics
Generate a strategic AI analysis
Example Output
## Macro Research Signals
Increased focus on chronic disease management and digital monitoring tools...

## Innovation Maturity Assessment
Pipeline skewed toward early-stage research with limited late-stage commercialization...

## Sponsor Power Dynamics
Academic institutions dominate; limited industry engagement observed...

## 3–5 Year Outlook
Shift toward remote monitoring and cost-effectiveness-driven innovation...
Requirements (Optional)
Create a requirements.txt:
requests>=2.28.0
openai>=1.0.0
python-dotenv>=0.19.0
**Install with:
pip install -r requirements.txt
**How It Works
API Ingestion – Pulls structured JSON trial data
Data Normalization – Extracts and flattens nested fields
Metric Computation – Calculates phase and sponsor distributions
AI Analysis – Combines structured data + summaries into a strategic report
**Important Notes
API Costs
Uses GPT-4o-mini (low-cost model)
One request per run
Monitor usage at: https://platform.openai.com/usage
Rate Limits
ClinicalTrials.gov API is public and does not require authentication
OpenAI usage depends on your plan
Possible Improvements
Compare two conditions side-by-side
Filter by recent trials (e.g., last 2 years)
Add visual charts for phase distribution
Export analysis as PDF
Build a Streamlit dashboard
Disclaimer
This tool is for educational and analytical purposes. It provides AI-generated strategic interpretations of publicly available clinical trial data and should not be used for medical decision-making.
