from website_scraper import scrape_website
from openai import OpenAI
MODEL = "llama3.1:8b"

ollama = OpenAI(base_url= "http://localhost:11434/v1", api_key= "ollama")

system_prompt = """
    You are an expert trader financial stock analyst.
    Your job:
- Analyze stock-related content
- Ignore navigation or irrelevant text
- Give a clear decision: BUY, HOLD, or AVOID
Respond in markdown. Do not wrap the markdown in a code block - respond just with the markdown.
"""

def user_prompt_for(website):
    user_prompt = f"You are looking at information of a stock from website titled {website.title}"
    user_prompt+= f"\nThe contents of the stock is as follows: "
    user_prompt += """\n Analyze the stock and respond with:
                        - Decision: BUY / HOLD / AVOID\n\n"""
    user_prompt+=website.text
    return user_prompt

def Analysis(url):
    website = scrape_website(url)
    response = ollama.chat.completions.create(
        model = MODEL,
        messages = [
            {"role":"system" , "content": system_prompt},
            {"role": "user", "content": user_prompt_for(website)}
        ]
    )
    return response.choices[0].message.content

def main():
    stock = input("Enter the website url: ")
    anal = Analysis(stock)
    print(anal)

if __name__ == "__main__":
    main()

