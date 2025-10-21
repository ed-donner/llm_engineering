# **Automated Bitcoin Daily Summary Generator**

This project automates the process of generating a daily summary of the Bitcoin network's status. It fetches real-time data from multiple public API endpoints, processes it, and then uses a Large Language Model (LLM) to generate a clear, structured, and human-readable report in Markdown format.

## **Project Overview**

The core goal of this project is to provide a snapshot of key Bitcoin metrics without manual analysis. By leveraging the Braiins Public API for data and OpenAI's GPT models for summarization, it can produce insightful daily reports covering market trends, network health, miner revenue, and future outlooks like the next halving event.

### **Key Features**

- **Automated Data Fetching**: Pulls data from 7 different Braiins API endpoints covering price, hashrate, difficulty, transaction fees, and more.
- **Data Cleaning**: Pre-processes the raw JSON data to make it clean and suitable for the LLM.
- **Intelligent Summarization**: Uses an advanced LLM to analyze the data and generate a structured report with explanations for technical terms.
- **Dynamic Dating**: The report is always dated for the day it is run, providing a timely summary regardless of the timestamps in the source data.
- **Markdown Output**: Generates a clean, well-formatted Markdown file that is easy to read or integrate into other systems.

## **How It Works**

The project is split into two main files:

1. **utils.py**: A utility script responsible for all data fetching and cleaning operations.
   - It defines the Braiins API endpoints to be queried.
   - It contains functions to handle HTTP requests, parse JSON responses, and clean up keys and values to ensure consistency.
2. **day_1_bitcoin_daily_brief.ipynb**: A Jupyter Notebook that acts as the main orchestrator.
   - It imports the necessary functions from utils.py.
   - It calls fetch_clean_data() to get the latest Bitcoin network data.
   - It constructs a detailed system and user prompt for the LLM, explicitly instructing it on the desired format and, crucially, to use the current date for the summary.
   - It sends the data and prompt to the OpenAI API.
   - It receives the generated summary and displays it as formatted Markdown.

## **Setup and Usage**

To run this project, you will need to have Python and the required libraries installed.

### **1\. Prerequisites**

- Python 3.x
- Jupyter Notebook or JupyterLab

### **2\. Installation**

- Install the necessary Python libraries: pip install requests openai python-dotenv jupyter

### **3\. Configuration**

You need an API key from OpenAI to use the summarization feature.

1. Create a file named .env in the root directory of the project.
2. Add your OpenAI API key to the .env file as follows:  
   OPENAI_API_KEY='your_openai_api_key_here'
