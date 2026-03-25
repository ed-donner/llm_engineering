# Developed by Renan Santos - Full lab: https://github.com/RenanSantos89/llm-engineering-lab

import pandas as pd
import ollama
from bs4 import BeautifulSoup
import requests
import os
from utils import format_log

CONFIG = {
    "MODEL": "smollm2:135m",
    "DATA_LAKE_PATH": "data_lake/summaries.parquet",
    "MAX_CHARS": 8000
}

def fetch_content(url):
    """Extracts raw text from a specific URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        for script_or_style in soup(["script", "style"]):
            script_or_style.extract()

        texto = soup.get_text(separator=" ", strip=True)
        
        return texto[500:CONFIG["MAX_CHARS"] + 500] 
        
    except Exception as e:
        print(format_log(f"Error accessing site: {e}"))
        return None

def summarise_content(text):
    """Generates a summary using the local LLM model."""

    prompt = f"Please summarise the following content concisely in english british: {text}"
    response = ollama.generate(model=CONFIG["MODEL"], prompt=prompt)
    return response['response']

def save_to_parquet(url, summary):
    """Persists the processed data into a local Data Lake (Parquet format)."""
    new_record = pd.DataFrame([{
        "url": url,
        "summary": summary,
        "timestamp": pd.Timestamp.now()
    }])
    
    os.makedirs(os.path.dirname(CONFIG["DATA_LAKE_PATH"]), exist_ok=True)
    
    if os.path.exists(CONFIG["DATA_LAKE_PATH"]):
        df_existing = pd.read_parquet(CONFIG["DATA_LAKE_PATH"])
        df_final = pd.concat([df_existing, new_record], ignore_index=True)
    else:
        df_final = new_record
        
    df_final.to_parquet(CONFIG["DATA_LAKE_PATH"], index=False)
    print(format_log(f"Data successfully organised and saved to: {CONFIG['DATA_LAKE_PATH']}"))

if __name__ == "__main__":
    # Feel free to change this URL to test
    target_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    print(format_log(f"Starting analysis for: {target_url}"))
    
    raw_text = fetch_content(target_url)
    if raw_text:
        summary_result = summarise_content(raw_text)
        save_to_parquet(target_url, summary_result)
        print(format_log("PREVIEW OF THE SUMMARY:"))
        print(summary_result)
        