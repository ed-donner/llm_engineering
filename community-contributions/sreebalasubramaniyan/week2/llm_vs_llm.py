"""
llm1 vs llm2 both from open router

there will be a message pool, each time the llm gives 
response based on the conversation so far

and the same reponse will also be loaded and the next llm will give the next response

conversation =[
llm1: "hi"

]

system_prompt = you are an agent who is very agressive at arguing
and you will be given the conversation of you(llm2) and your companien(llm1)
based on that conversation you should reply to your companien
"""



import os
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
apikey = os.getenv("OPENROUTER_API_KEY")
print(apikey)
openrouter = OpenAI(base_url="https://openrouter.ai/api/v1",api_key=apikey)
model1 = "cohere/north-mini-code:free"
model2 = ""

conversation = ["""
llm2 : hi how are you?
"""]

def LLM1():
    system_prompt = """you are an agent who is very agressive at arguing
    and you will be given the conversation of you(llm1) and your companien(llm2).
    based on that conversation you should reply to your companien.(only give the response don't need to add llm1:) and keep the response very small and yet effective
    be so rude and agreesive and use american hood accent
    """

    llm1_response = openrouter.chat.completions.create(
        model = model1,
        messages = [{"role":"system","content":system_prompt},{"role":"user","content":conversation[0]}]
    )

    res = (llm1_response.choices[0].message.content)
    print(f"llm1: {res}",end="\n\n")
    conversation[0] += f"llm1: {res}"
  

def LLM2():
    system_prompt = """you are an agent who is very agressive at arguing
    and you will be given the conversation of you(llm2) and your companien(llm1).
    based on that conversation you should reply to your companien.(only give the response don't need to add llm2:) and keep the response very small and yet effective
    """

    llm2_response = openrouter.chat.completions.create(
        model = model1,
        messages = [{"role":"system","content":system_prompt},{"role":"user","content":conversation[0]}]
    )

    res = (llm2_response.choices[0].message.content)
    print(f"llm2: {res}",end="\n\n")
    conversation[0] += f"llm2: {res}"
    

def cycle():
    LLM1()
    LLM2()

for i in range(5):
    cycle()

