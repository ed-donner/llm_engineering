
from openai import OpenAI
from website_scraper import scrape_website

ollama = OpenAI(base_url="http://localhost:11434/v1", api_key='ollama')
Model = "llama3.1:8b"

system_prompt = """
You are a higly knowlegeable share trader and assistant.
Your job:
- Analyze stock-related content
- Ignore navigation or irrelevant text
- Give a clear decision: BUY, HOLD, or AVOID
- Keep it short and sharp
Respond in markdown. Do not wrap the markdown in a code block - respond just with the markdown.
"""
def user_prompt(website):
    user_prompt = f"You are looking at a website titled {website.title}"
    user_prompt+= "\nThe contents of the website is as follows:"
    user_prompt += """\n Analyze the stock and respond with:
                        - Decision: BUY / HOLD / AVOID\n\n"""
    user_prompt+=website.text[:4000]
    return user_prompt

def get_stock_info(url):
    website_url= scrape_website(url)
    response = ollama.chat.completions.create(
        model = Model,
        messages = [
            {"role":"system" , "content":system_prompt},
            {"role": "user" , "content": user_prompt(website_url)}  
        ]
    )
    return response.choices[0].message.content

def main():
    website_url  = input("Enter the website url: ")
    summm = get_stock_info(website_url)
    print(summm)

if __name__ == "__main__":
    main()




