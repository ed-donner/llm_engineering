import os
from secretapikey import API_Key
from mistralai import Mistral
from pypdf import PdfReader

def get_file_content(path):
    if path.endswith(".pdf"):
        reader = PdfReader(path)
        return "\n".join([p.extract_text() for p in reader.pages])
    else:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

client = Mistral(api_key=API_Key)

my_file = "/Users/charu/Downloads/GenEnq.pdf" 
document_text = get_file_content(my_file)

system_prompt = "You are an expert summarizer. Create a notebook-style summary with page references."
user_prompt = f"Please summarize the following document:\n\n{document_text}"

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt}
]

response = client.chat.complete(
    model="mistral-large-latest", 
    messages=messages
)

print(response.choices[0].message.content)