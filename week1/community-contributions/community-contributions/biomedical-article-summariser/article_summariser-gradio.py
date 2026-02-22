import re

import requests
import functools
from typing import List, Tuple, Dict, Any

from loguru import logger

from bs4 import BeautifulSoup as bs


import ollama
import gradio as gr



SYS_PROMPT = """
You are an expert in biomedical text mining and information extraction. 
You excel at breaking down complex articles into digestible contents for your audience. 
Your audience can comprise of students, early researchers and professionals in the field.
Summarize the key findings in the following article [ARTICLE] .
Your summary should provide crucial points covered in the paper that helps your diverse audience quickly understand the most vital information. 
Crucial points to include in your summary:
- Main objectives of the study
- Key findings and results
- Methodologies used
- Implications of the findings(if any)
- Any limitations or future directions mentioned

Format: Provide your summary in bullet points highlighting key areas followed with a concise paragraph that encapsulates the results of the paper.

The tone should be professional and clear.

"""




def catch_request_error(func):
    """
    Wrapper func to catch request errors and return None if an error occurs.
    Used as a decorator.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.RequestException as e:
            print(f"Request error in {func.__name__}: {e}")
            return None
    return wrapper



@catch_request_error
@logger.catch
def get_xml_from_url(url: str) -> bs:
    """
    Fetches the XML content from Europe PMC website.

    Args:
        url (str): Europe PMC's production url to fetch the XML from.

    Returns:
        soup (bs4.BeautifulSoup): Parsed XML content.
    """
    response = requests.get(url)
    response.raise_for_status() #check for request errors
    return bs(response.content, "lxml-xml")  




def clean_text(text:str) -> str:
    """
    This function cleans a text by filtering reference patterns in text, 
    extra whitespaces, escaped latex-style formatting appearing in text body instead of predefined latex tags

    Args: 
    text(str): The text to be cleaned
    
    Returns: 
    tex(str): The cleaned text 
    
    """
   
    # Remove LaTeX-style math and formatting tags #already filtered from soup content but some still appear
    text = re.sub(r"\{.*?\}", "", text)  # Matches and removes anything inside curly braces {}
    text = re.sub(r"\\[a-zA-Z]+", "", text)  # Matches and removes characters that appears with numbers
    
    # Remove reference tags like [34] or [1,2,3]
    text = re.sub(r"\[\s*(\d+\s*(,\s*\d+\s*)*)\]", "", text)
    
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    return text


def fetch_article_abstract(soup: bs) -> Tuple[str, str]:
    """
    Extracts the abstract text from the XML soup.

    Args:
        soup (bs4.BeautifulSoup): Parsed XML content.
    Returns:
        Tuple(article_title (str), abstract_text (str)): A tuple of the article's title and its extracted abstract text.
    """
    if soup is None:
        return "No XML found", ""
    article_title = soup.find("article-title").get_text(strip=True) if soup.find("article-title") else "No Title Found for this article"

    abstract_tag = soup.find("abstract")
    if abstract_tag:
        abstract_text = ' '.join([clean_text(p.get_text(strip=True)) for p in abstract_tag.find_all("p") if p.get_text(strip=True)])
    else:
        abstract_text = ""
    return article_title, abstract_text



def build_message(article_title: str, abstract_text: str, sys_prompt:str=SYS_PROMPT) -> List[Dict[str, str]]:
    """
    Constructs the message payload for the LLM.

    Args:
        article_title (str): The title of the article.
        abstract_text (str): The abstract text of the article.

    Returns:
        List[Dict[str, str]]: A list of message dictionaries for the LLM.
    """
    user_prompt = f"""You are looking at an article with title:  {article_title}. 
    The article's abstract is as follows: \n{abstract_text}.
    Summarise the article. Start your summary by providing a short sentence on what the article is about 
    and then a bulleted list of the key points covered in the article.
"""
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return messages



def generate_response(messages:List[Dict[str, str]], model:str) -> str:
    """ 
    Generates a response from the LLM based on the provided messages.
    Args:
        messages (List[Dict[str, str]]): The message payload for the LLM.
        model (str): The model to use for generating the response.
    Returns:
        str: The content of the LLM's response.
    """

    response = ollama.chat(model=model, messages=messages)
    return response["message"]["content"]


def summariser(article_id: str, model:str) -> str:
    if article_id and not re.match(r"^PMC\d{5,8}$", article_id):
        raise gr.Error("Please check the length/Format of the provided Article ID. It should start with 'PMC' followed by 5 to 8 digits, e.g., 'PMC1234567'.")
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{article_id}/fullTextXML"
    soup = get_xml_from_url(url)
    article_title, abstract_text = fetch_article_abstract(soup)
    if not abstract_text:
         raise gr.Error(f"No abstract found for {article_title}")
    messages = build_message(article_title, abstract_text)

    #pull model from ollama
    ollama.pull(model)
    summary = generate_response(messages, model)

    return f"## 📝 Article Title: {article_title}\n\n### 📌 Summary:\n{summary}"

INTRO_TXT = "This is a simple Biomedical Article Summariser. It uses PMCID to fetch articles from the Europe PMC(EPMC) Website. It currently only runs on article's abstract. Future improvements would integrate full-text articles"
INST_TXT = "Enter a **EuropePMC Article ID** (e.g., `PMC1234567`) and select a model from the dropdown menu to generate a structured summary"
def gradio_ui():
  with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown(INTRO_TXT)
    gr.Markdown(INST_TXT)

    with gr.Row():
      with gr.Column(scale=1):
        article_id = gr.Textbox(label="Enter Article's PMCID here", placeholder="e.g., PMC1234567")
        model_choice = gr.Dropdown(choices=["llama3.2", "deepseek-r1", "gemma3", "mistral", "gpt-oss"], value="llama3.2", label="Select a model")
        run_btn = gr.Button("Fetch Article Abstract and generate Summary", variant='primary')
      with gr.Column(scale=1):
        output_box = gr.Markdown()


    run_btn.click(fn=summariser, inputs=[article_id, model_choice], outputs=output_box)
  
  return demo


if __name__ == "__main__":
  app = gradio_ui()
  app.launch(share=True, debug=True)



