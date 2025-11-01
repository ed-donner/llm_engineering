# python newbie, just playing around with creating the illusion of memory
from openai import OpenAI
openai=OpenAI()

message=[{"role":"system","content":"you are a sarcastic assistant"}]

while True:
    userinput=input("Enter msg: ")
    message.append({"role":"user","content":userinput})
    response=openai.chat.completions.create(model="gpt-4.1-mini", messages=message)
    print(response.choices[0].message.content)
    message.append({"role":"assistant","content":response.choices[0].message.content})
