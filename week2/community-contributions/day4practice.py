
import os 
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
import json
from openai._utils import required_args
import sqlite3

load_dotenv(override=True)
openai=OpenAI()
api_key=os.getenv("OPENAI_API_KEY")


# menu={"panipuri":"10$","dahipuri":"15$","bhelpuri":"20$","pavbhaji":"30$","vadapav":"10$"}

# def getmenu(item):
#     print(f'''Tool called for {item}''')
#     price=menu.get(item.lower(),"Unknown item")
#     return f'''The price of {item} is {price}'''

system_message="You are a helpful assistant for a restaurant. You should respond politely in simple responses"


menufunction={
    "name":"getmenu",
    "description":"Gets the price of the menu selected",
    "parameters":{
        "type":"object",
        "properties":{
            "item":{
                "type":"string",
                "description":"The item user selected to purchase",
            },
        },
        "required":["item"],
        "additionalProperties":False
    }
}

setmenufunction={
    "name":"setprice",
    "description":"Sets the price of the item in menu",
    "parameters":{
        "type":"object",
        "properties":{
            "item":{
                "type":"string",
                "description":"The item that needs to be included in menu"
            },
            "price":{
                "type":"number",
                "description":"The price of the item "
            }
        },
        "additionalProperties":False,
        "required":["item","price"]
    }
}


tools=[{"type":"function","function":menufunction},{"type":"function","function":setmenufunction}]

def handle_tool_call(message):
    response=[] 
    for tool_call in message.tool_calls:
        if tool_call.function.name=='getmenu':
            argument=json.loads(tool_call.function.arguments)
            print(argument)
            item=argument.get('item')
            price=getmenu(item)
            response.append(
                {
                    "role":"tool",
                    "content":price,
                    "tool_call_id":tool_call.id
                }
            )
        if tool_call.function.name=='setprice':
            argument=json.loads(tool_call.function.arguments)
            print(argument)
            item=argument.get('item')
            price=argument.get('price')
            setprice(item,price)
            response.append(
                {
                    "role":"tool",
                    "content":f'''The price of {item} is set to {price}''',
                    "tool_call_id":tool_call.id
                }
            )
    return response



def getOutput(message,history):
    history=[{"role":h['role'],"content":h['content']} for h in history]
    messages=[{"role":"system","content":system_message}]+history+[{"role":"user","content":message}]
    response=openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        tools=tools
    )
    while response.choices[0].finish_reason=='tool_calls':
        print(response.choices[0].message)
        message=response.choices[0].message
        responses=handle_tool_call(message)
        messages.append(message)
        messages.extend(responses)
        response=openai.chat.completions.create(model='gpt-5-nano',messages=messages,tools=tools)
    return response.choices[0].message.content


DB = "prices.db"

with sqlite3.connect(DB) as conn:
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS prices (item TEXT PRIMARY KEY, price REAL)')
    conn.commit()

def getmenu(item):
    print(f"DATABASE TOOL CALLED: Getting price for {item}", flush=True)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT price FROM prices WHERE item = ?', (item.lower(),))
        result = cursor.fetchone()
        return f"The price of  {item} is ${result[0]}" if result else "No price data available for this city"


def setprice(item, price):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO prices (item, price) VALUES (?, ?) ON CONFLICT(item) DO UPDATE SET price = ?', (item.lower(), price, price))
        conn.commit()
       


# menu={"panipuri":10,"dahipuri":15,"bhelpuri":20,"pavbhaji":30,"vadapav":10}

# for item,price in menu.items():
#     setprice(item,price)
    


gr.ChatInterface(fn=getOutput,type="messages").launch(inbrowser=True)