# Initialization
# imports

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
import sqlite3
load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")
    
MODEL = "gpt-4.1-mini"
openai = OpenAI()

DB = "prices.db"



system_message = """
You are a helpful assistant for an Airline called FlightAI.
Give short, courteous answers, no more than 1 sentence.
Always be accurate. If you don't know the answer, say so.
"""
database = "prices.db"
def get_ticket_price_db(city):
    with sqlite3.connect(database) as conn:
        cursor=conn.cursor()
        cursor.execute("select price from prices where city=?",(city,))
        result=cursor.fetchone()
        return f"the ticket price for {city} is {result[0]}" if result else "unknow ticket price"

with sqlite3.connect(DB) as conn:
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS prices (city TEXT PRIMARY KEY, price REAL)')
    conn.commit()

def set_ticket_price(city, price):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO prices (city, price) VALUES (?, ?) ON CONFLICT(city) DO UPDATE SET price = ?', (city.lower(), price, price))
        conn.commit()

ticket_prices = {"london":799, "paris": 899, "tokyo": 1420, "sydney": 2999}
for city, price in ticket_prices.items():
    set_ticket_price(city, price)


ticket_price={
    "name":"get_ticket_price_db",
    "description":"this function is used to return the price ticket for a city",
    "parameters":
    {
      "type":"object",
      "properties":
      {
        "destination_city":{
          
        "type":"string",
        "description":"the name of the city"
    }},
    "additionalProperties":False,
    "required":["destination_city"]
}
}

tools=[{"function":ticket_price, "type":"function"}]

def handle_call_db(message):
    response=[]
    cities=[]
    for tool in message.tool_calls:
        if tool.function.name=="get_ticket_price_db":
            args=json.loads(tool.function.arguments)
            city=args["destination_city"]
            cities.append(city)
            result=get_ticket_price_db(city.lower())
            response.append({
                "role":"tool",
                "content":result,
                "tool_call_id":tool.id
            })
    return response, cities

def chat(history):
    cities=[]
    image=None
    history=[{"role": h["role"], "content": h['content']} for h in history]
    messages=[{"role": "system", "content": system_message}]+history
    response=openai.chat.completions.create(
        model=MODEL, messages=messages, tools=tools
    )

    while response.choices[0].finish_reason=="tool_calls":
        message=response.choices[0].message
        
        result, cities =handle_call_db(message)
        messages.append(message)
        messages.extend(result)
        response=openai.chat.completions.create(
        model=MODEL, messages=messages, tools=tools
        )
    result= response.choices[0].message.content
    history+=[{"role":"assistant", "content":result}]

    if result:
        audio=chat_to_audio(result)
    if cities:
        image=artist(city[0])
    return history,audio,image

def chat_to_audio(message):
    response=openai.audio.speech.create(
     model="gpt-4o-mini-tts",
    voice="onyx",    # Also, try replacing onyx with alloy or coral
    input=message
    )

    return response.content
import base64
from io import BytesIO
from PIL import Image

def artist(city):
    response=openai.images.generate(
     model="dall-e-3",
     prompt=f"An image representing a vacation in {city}, showing tourist spots and everything unique about {city}, in a vibrant pop-art style",
     size='1024x1024',
     n=1,
     response_format='b64_json'
    )

    image_b64 =response.data[0].b64_json
    image=base64.b64decode(image_b64)
    return Image.open(BytesIO(image))

def add_chat_message(message, history):
    return "", history+ [{"role":"user", "content":message}]

with gr.Blocks() as ui:
    gr.Markdown('multiple calls')
    with gr.Row():
        chatbot=gr.Chatbot(height=512, type="messages")
        image=gr.Image(height=512, interactive=True)
    with gr.Row():
        audio=gr.Audio(autoplay=True)
    with gr.Row():
        message=gr.Text(label='Chat with our AI Assistant:')
    
    message.submit(fn=add_chat_message, inputs=[message,chatbot], outputs=[message,chatbot]).then(
    fn=chat, inputs=[chatbot]  ,outputs=[chatbot,audio, image]

    )

    ui.launch(inbrowser=True, auth=['salma','salma'])
    

