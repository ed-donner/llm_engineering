import os
import time
from dotenv import load_dotenv  # Add this import
load_dotenv()
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def scrape_page(url):
    options = Options()
    options.add_argument("--disable-gpu")
    
    
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    
    print(f"\n [1/2] Fetching page content from: {url}")
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(url)
        
        
        time.sleep(5)
        
        paragraphs = driver.find_elements(By.TAG_NAME, "p")
        text = " ".join([p.text for p in paragraphs if len(p.text.strip()) > 30])
        return text
    except Exception as e:
        print(f"Scraping failed: {e}")
        return ""
    finally:
        driver.quit()

def generate_groq_summary(text):
    api_key = os.environ.get("GROQ_API_KEY")

    headers = {
          "Authorization": f"Bearer {api_key}",
          "Content-Type": "application/json"
           }
    if not text or len(text.strip()) < 50:
        return " Error: No usable article text was extracted by the scraper."
        
    print(" [2/2] Sending text to ultra-fast Groq Cloud AI...")
    
    groq_url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "user",
                "content": f"Provide a concise, professional summary of the following web article using bullet points:\n\n{text}"
            }
        ]
    }
    
    try:
        response = requests.post(groq_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"\nGroq API Error (Status Code {response.status_code}):")
            print(response.text)
            return " Summary generation failed due to an API error."
            
        result = response.json()
        return result['choices'][0]['message']['content']
        
    except Exception as e:
        return f" Network connection to Groq failed entirely! Error: {e}"

if __name__ == "__main__":
    target_url = "https://modernfamily.fandom.com/wiki/Modern_Family_Wiki"
    
    article_text = scrape_page(target_url)
    summary = generate_groq_summary(article_text)
    
    print("\n FINAL AI SUMMARY RESULT:")
    print("--------------------------------------------------")
    print(summary)
    print("--------------------------------------------------\n")