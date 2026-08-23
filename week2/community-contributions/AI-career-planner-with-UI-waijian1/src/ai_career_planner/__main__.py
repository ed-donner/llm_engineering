import os
import csv
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv(override=True)

from ai_career_planner.jobsearchapi import extract_job_details

#Load country listing
def load_country_dict():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'country_code_listing.csv')

    country_dict = {}

    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)

        for row in reader:
            if len(row) < 2:
                continue

            code = row[-1].strip()  # last column
            country = ",".join(row[:-1]).strip()  # join the rest

            country_dict[country] = code

    return country_dict

COUNTRY_DICT = load_country_dict()
COUNTRY_LIST = list(COUNTRY_DICT.keys())

#Gemini API Setup
GEMINI_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta/openai/'
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')
gemini = OpenAI(base_url=GEMINI_BASE_URL, api_key=GEMINI_API_KEY)
GEMINI_MODEL = 'gemini-3.1-flash-lite-preview'

#Ollama API Setup
OLLAMA_BASE_URL = 'http://localhost:11434/v1'
OLLAMA_API_KEY = 'ollama' # can be any words, not important
ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)
OLLAMA_MODEL = 'gpt-oss:latest'

def create_career_plan(job_title, model, country, stream):
    #Validate job title
    if not job_title:
        yield '### Please input a valid job title...'
        return

    #Validate model
    selected_model = None

    if model == "Gemini":
        model = GEMINI_MODEL
        selected_model = gemini

    elif model == "Ollama":
        model=OLLAMA_MODEL
        selected_model = ollama
    
    else:
        yield f'### Please select a model before proceeding...'
        return

    #Validate country
    if not COUNTRY_DICT.get(country):
        yield '### Please select a valid country...'
        return

    yield f'### Searching active job posting from {country}'
    active_job = extract_job_details(job_title=job_title, country=country, country_code=COUNTRY_DICT[country])

    #Construct system prompt
    system_prompt = """
    You are a helpful education coach to help to design a professional 4 weeks plan for the user based on the job title. 
    If the job title is not valid, please say so and ask user to input the correct job title again. 
    If the job title is valid, Response in markdown. Do not wrap the markdown with code block - reply only in markdown.
    """

    #Construct user prompt
    user_prompt = f"""
    You will be provided a list of extracted similar job from the list below.
    List of active job available in the user country:
    {active_job}
    If there are no job found from the user country, please notify the user.
    You will analyze the job title provided by user, think thoroughly before providing a professional 4 weeks plan regarding the structures of the learning path, provide useful link for the learning & tips to achieve success for the user based on the job requirements from similar job provided above.
    Highlight the most frequent or top few job requirements / skills needed from most company extracted above.
    Lastly, from the list of active job above, highlight the top 5 companies name, their website, job apply link & their required skill in the last section.
    This is the job title user wish to expertise on:
    Job Title: {job_title}
    """

    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt}
    ]

    print(f'Creating a 4-week plan for {job_title} using model {model}...')
        
    if not stream:
        response = selected_model.chat.completions.create(model=model, messages=messages)
        result = response.choices[0].message.content
        yield "### Your personalized study plan:\n" + result
        return

    else:
        stream = selected_model.chat.completions.create(model=model, messages=messages, stream=True)
        response = "### Your personalized study plan:\n"

        for chunk in stream:
            response += chunk.choices[0].delta.content or ''
            yield response

# Launch Gradio App
message_input = gr.Textbox(label="Job Title", info="Enter your job title to create study plan", lines=3)

model_selector = gr.Radio(
    choices=["Ollama", "Gemini"],
    value="Ollama",
    label="Select Model"
)

stream_toggle = gr.Checkbox(
    label="Streaming",
    value=True
)

country = gr.Dropdown(
    label='Country',
    choices=COUNTRY_LIST,
    value='Singapore',
)

message_output = gr.Markdown()

view = gr.Interface(
    fn=create_career_plan,
    title="AI career planner",
    inputs=[message_input, model_selector, country, stream_toggle],
    outputs=[message_output],
    examples=[
        ["AI Engineer", "Ollama", 'Singapore', True],
        ["Financial Advisor", "Gemini", 'Malaysia', False]
    ],
    flagging_mode="never"
)

view.launch(
    inbrowser=True, 
    # auth=(os.getenv('GRADIO_ID'),os.getenv('GRADIO_PW')),
    # share=True
)