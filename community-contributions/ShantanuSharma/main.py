from google import genai
from dotenv import load_dotenv
import os
from scraper import fetch_website_contents


load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")


if not api_key:
    print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
else:
    print("API key found and looks good so far!")
    client = genai.Client(api_key=api_key.strip())

website = "https://pulse.zerodha.com/"

website_content = fetch_website_contents(website)

prompt_message = f"""
Here is a website to learn latest news in the Finance domain.
Use the website to gather insights and then do fundamental analysis of the companies in the news. 
Finally, recommend stocks to buy or sell based on the analysis.
Rely on facts and data to make your recommendations.
{website_content}
"""

system_message = """
You are a stock market analyst. Provide insights based on the user's query.
"""


response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt_message,
    config=genai.types.GenerateContentConfig(
        system_instruction=system_message,
        temperature=0.2,
    ),
)

print(response.text)
