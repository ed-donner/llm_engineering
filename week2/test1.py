
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
import sqlite3
# Initialization

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")
    
MODEL = "gpt-4.1-mini"
openai = OpenAI()

# As an alternative, if you'd like to use Ollama instead of OpenAI
# Check that Ollama is running for you locally (see week1/day2 exercise) then uncomment these next 2 lines
# MODEL = "llama3.2"
# openai = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
system_message = """
You are a helpful assistant for an Airline called FlightAI.
Give short, courteous answers, no more than 1 sentence.
Always be accurate. If you don't know the answer, say so.
"""

price_function={
        "name": "get_ticket_price",
        "description": "Retrieves a ticket price for a given city from the 'ticket_prices' dictionary and returns a formatted string.",
        "parameters": {
            "type":"object",
            "properties":{
                "destination_city":{
                "type":"string",
                "description": "The name of the city the user wants to check the ticket price for."
            },
            },
            "required":['destination_city'],
            "additionalProperties":False
        },
   
    }
get_price_function_db={
        "name": "get_ticket_price_db",
        "description": "Retrieves a ticket price for a given city from the 'ticket_prices' dictionary and returns a formatted string.",
        "parameters": {
            "type":"object",
            "properties":{
                "city":{
                "type":"string",
                "description": "The name of the city the user wants to check the ticket price for."
            },
              },
            "required":['city'],
            "additionalProperties":False
        }}
set_price_function_db={
         "name": "set_ticket_price_db",
        "description": "set a ticket price for a given city.",
        "parameters": {
            "type":"object",
            "properties":{
                "city":{
                "type":"string",
                "description": "The name of the city the user wants to add or update on conflict"
            },
             "price":{
                "type":"string",
                "description": "The price of the ticket for the city."
            },
            },
            "required":['city','price'],
            "additionalProperties":False
        },
   
    }
ticket_prices={"london":"$799", "paris":"$900", "tokyo":"$1200","sydney":"$2000"}
database='prices.db'
def set_ticket_prices_db(city, price):
    with sqlite3.connect(database) as conn:
        cursor=conn.cursor()
        result=cursor.execute('insert into prices (city, price) values (?,?) on conflict do update set price=?',(city.lower(),price,price))
        conn.commit()
        return get_ticket_prices_db(city.lower())
         
def get_ticket_prices_db(city):
    with sqlite3.connect(database) as conn:
        cursor=conn.cursor()
        cursor.execute('select price from prices where city=?', (city,))
        result=cursor.fetchone()
        return f'ticket price for {city} = {result[0]}' if result else 'unknown'

with sqlite3.connect(database) as conn:
    cursor=conn.cursor()
    cursor.execute("create table if not exists prices (city text primary key, price real)")
    conn.commit()
ticket_prices={"london":"$799", "paris":"$900", "tokyo":"$1200","sydney":"$2000"}
for city in ticket_prices:
   set_ticket_prices_db(city, ticket_prices[city])




def get_ticket_price(city):
    print(f"call to get_ticket_price for {city}")
    ticket_price=ticket_prices.get(city.lower(),"Ticket price is unknow ")
    return f"tiket price to {city} is {ticket_price}"

tool_name={"function":price_function, "type":"function"}


tools=[{"function":get_price_function_db, "type":"function"},{"function":set_price_function_db, "type":"function"}]
def handler_call(message):
    function=message.tool_calls[0]
    if function.function.name=="get_ticket_prices":
        arguments=json.loads(function.function.arguments)
        city=arguments['destination_city']
        ticket_price=get_ticket_price(city)
        response={
            "role":"tool",
            "content":ticket_price,
            "tool_call_id":function.id
        }
        return response

def handler_call_db(message):

    def handle_get_price_db(tool_call):
        arguments=json.loads(tool_call.function.arguments)
        city=arguments['city']
        ticket_price=get_ticket_prices_db(city.lower())
        return ticket_price

    def handle_set_price_db(tool_call):
        arguments=json.loads(tool_call.function.arguments)
        city=arguments['city']
        price=arguments['price']
        ticket_price=set_ticket_prices_db(city,price)
        return ticket_price

    handler={"get_ticket_price_db":handle_get_price_db,"set_ticket_price_db":handle_set_price_db}


    
    response=[] 
    for tool_call in message.tool_calls:
        function=handler.get(tool_call.function.name)
        if function:
            ticket_price=function(tool_call)
        #if tool_call.function.name=="get_ticket_price_db":
            #arguments=json.loads(tool_call.function.arguments)
            #city=arguments['city']
            #ticket_price=get_ticket_prices_db(city.lower())
        response.append({
                "role":"tool",
                "content":ticket_price,
                "tool_call_id":tool_call.id
            })
            
            
        #elif tool_call.function.name=="set_ticket_price_db":
           
            #response.append({
            #    "role":"tool",
            #    "content":"ticket price was set for {city}",
            #    "tool_call_id":tool_call.id
            #})
    return response
   


def chat(message, history):
    history = [{"role":h["role"], "content":h["content"]} for h in history]
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=MODEL, messages=messages, tools=tools)
    while response.choices[0].finish_reason=="tool_calls":
        message=response.choices[0].message
        response=handler_call_db(message)
        messages.append(message)
        messages.extend(response)
   
        response=openai.chat.completions.create(model=MODEL, messages=messages,tools=tools)
    return response.choices[0].message.content
        

gr.ChatInterface(fn=chat, type="messages").launch()
