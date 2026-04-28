# imports

import os
from dotenv import load_dotenv
# from scraper import fetch_website_contents
from IPython.display import Markdown, display
from openai import OpenAI

# If you get an error running this cell, then please head over to the troubleshooting notebook!

# Load environment variables in a file called .env

load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

# Check the key

if not api_key:
    print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
elif not api_key.startswith("sk-proj-"):
    print("An API key was found, but it doesn't start sk-proj-; please check you're using the right key - see troubleshooting notebook")
elif api_key.strip() != api_key:
    print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
else:
    print("API key found and looks good so far!")

# To give you a preview -- calling OpenAI with these messages is this easy. Any problems, head over to the Troubleshooting notebook.

def solve_problem(problem_text) :

    openai = OpenAI()


# Define our system prompt - you can experiment with this later, changing the last sentence to 'Respond in markdown in Spanish."

    system_prompt = """
    You are a top-level competitive programmer.

    The following is a coding problem extracted via OCR. It may contain noise or minor errors.

    Your task:
    1. Understand the intended problem correctly
    2. Fix any OCR mistakes mentally
    3. Provide:
    - Clean problem understanding (1-2 lines)
    - Optimal approach
    - Time & space complexity
    - Clean C++ solution
    """

    # Define our user prompt

    user_prompt_prefix = """
    This is the Problem :
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_prefix + problem_text}
    ]

    response = openai.chat.completions.create(model="gpt-5-nano", messages=messages)
    return response.choices[0].message.content

   

   

