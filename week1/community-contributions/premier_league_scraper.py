# Import necessary libraries
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from IPython.display import Markdown, display
from openai import OpenAI
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# The Premier League site builds the table with JavaScript, so requests + BeautifulSoup
# only sees an empty shell. Selenium drives a real (headless) Chrome so the table is rendered first.

def fetch_website_contents(url, wait_for="table tbody tr", timeout=20, max_chars=10_000):
    """
    Return the title and contents of the website at the given url after JavaScript has run;
    waits for the CSS selector wait_for to appear, and truncates to max_chars
    """
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)  # Selenium Manager downloads the matching chromedriver
    try:
        driver.get(url)
        try:
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_for)))
        except TimeoutException:
            print(f"Timed out waiting for '{wait_for}' - using whatever has loaded so far")
        soup = BeautifulSoup(driver.page_source, "html.parser")
    finally:
        driver.quit()

    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:max_chars]

# Load environment variables in a file called .env

load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

# Check OpenAI API key validity

if not api_key:
    print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
elif not api_key.startswith("sk-proj-"):
    print("An API key was found, but it doesn't start sk-proj-; please check you're using the right key - see troubleshooting notebook")
elif api_key.strip() != api_key:
    print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
else:
    print("API key found and looks good so far!")



# Step 1: Creating the prompt. It consists of two parts: the system prompt and the user prompt.
system_prompt = """You are a helpful assistant that can answer questions and help with tasks.
You are very experienced in English football and have a soft spot for Chelsea Football Club.
Provide responses in prettified visual format with the logos of the teams. Make sure lines are aligned properly."""

user_prompt = """
    Here is the Premier League website. Look out for the latest Premier League table and summarize. 
    Highlight Cheslea's position and tell me about the next upcoming game for Chelsea.
"""

premier_league = fetch_website_contents("https://www.premierleague.com/en/tables/premier-league/2026-27")
#print(premier_league)

# Step 2: Make the messages list

def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt + "\n\n" + website}
    ]

# print (messages_for(premier_league))

# Step 3: Call OpenAI (using gpt-6-luna model)
openai = OpenAI()

def summarize(url):
    website = fetch_website_contents(url)
    response = openai.chat.completions.create(
        model = "gpt-6-luna",
        reasoning_effort = "none",
        messages = messages_for(website)
    )
    return response.choices[0].message.content

# Step 4: print the result

print (summarize("https://www.premierleague.com/en/tables/premier-league/2026-27"))

# A function to display this nicely in the output, using markdown

def display_summary(url):
    summary = summarize(url)
    display(Markdown(summary))

display_summary("https://www.premierleague.com/en/tables/premier-league/2026-27")