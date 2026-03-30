import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from tools import (
    lookup_user_account,
    issue_refund,
    create_support_ticket,
)
from rag import search_knowledge_base
load_dotenv(override=True)


client = OpenAI()
MODEL = "gpt-4o-mini"
MAX_TOKENS = 1000

BLUE = "\033[94m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def router_agent(query, history=None):
    print(f"{BLUE}Router Agent received: {query}{RESET}")
    history = history or []

    tools = [
        {
            "type": "function",
            "function": {
                "name": "route_to_agent",
                "description": "Route the user query to the appropriate support agent.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "enum": ["billing_agent", "technical_agent", "knowledge_agent"],
                            "description": "The name of the agent to route the query to."
                        }
                    },
                    "required": ["agent_name"]
                }
            }
        }
    ]

    messages = [
        {"role": "system", "content": "You are a router agent. Route the user's query to the correct department based on the conversation history and the latest query."},
        *history,
        {"role": "user", "content": query}
    ]
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="required",
        max_tokens=MAX_TOKENS
    )

    tool_calls = response.choices[0].message.tool_calls
    if tool_calls:
        args = json.loads(tool_calls[0].function.arguments)
        return args.get("agent_name")
    
    return "knowledge_agent"


def billing_agent(query, history=None):
    print(f"{GREEN}Billing Agent received: {query}{RESET}")
    history = history or []
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "lookup_user_account",
                "description": "Look up user account details using their email address.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "The user's email address."
                        }
                    },
                    "required": ["email"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "issue_refund",
                "description": "Issue a refund for a specific order after verifying the user's account.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The ID of the order to be refunded."
                        },
                        "email": {
                            "type": "string",
                            "description": "The user's email address for verification."
                        }
                    },
                    "required": ["order_id", "email"]
                }
            }
        }
    ]

    messages = [
        {"role": "system", "content": "You are a billing support agent. Use the available tools to help the user. If you cannot perform the action, ask for missing details. IMPORTANT: Only return one tool call at a time, choosing the most important action to take next."},
        *history,
        {"role": "user", "content": query}
    ]
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        max_tokens=MAX_TOKENS
    )

    message = response.choices[0].message
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        tool_result = None
        
        if function_name == "lookup_user_account":
            tool_result = lookup_user_account(**arguments)
        
        elif function_name == "issue_refund":
            email = arguments.get("email")
            order_id = arguments.get("order_id")

            user_account = lookup_user_account(email)
            if "User not found" in str(user_account):
                tool_result = "Cannot issue refund: User account not found."
            else:
                tool_result = issue_refund(order_id=order_id)
            
        if tool_result:
            messages.append(message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(tool_result)
            })
            
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS
            )
            return response.choices[0].message.content
    
    return message.content


def technical_agent(query, history=None):
    print(f"{RED}Technical Agent received: {query}{RESET}")
    history = history or []

    tools = [
        {
            "type": "function",
            "function": {
                "name": "create_support_ticket",
                "description": "Create a support ticket for a technical issue.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "issue": {
                            "type": "string",
                            "description": "Description of the technical issue."
                        }
                    },
                    "required": ["issue"]
                }
            }
        }
    ]

    messages = [
        {"role": "system", "content": "You are a technical support agent. Create a ticket for technical issues."},
        *history,
        {"role": "user", "content": query}
    ]
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        max_tokens=MAX_TOKENS
    )

    message = response.choices[0].message
    if message.tool_calls:
        messages.append(message)
        for tool_call in message.tool_calls:
            arguments = json.loads(tool_call.function.arguments)
            tool_result = create_support_ticket(**arguments)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(tool_result)
            })

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS
        )
        return response.choices[0].message.content
        
    return message.content


def knowledge_agent(query, history=None):
    print(f"{YELLOW}Knowledge Agent received: {query}{RESET}")
    history = history or []

    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": "Search the knowledge base for answers to user questions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query."
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    messages = [
        {"role": "system", "content": "You are a knowledge base agent. Search for information to answer user questions."},
        *history,
        {"role": "user", "content": query}
    ]
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        max_tokens=MAX_TOKENS
    )

    message = response.choices[0].message
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)
        
        results = search_knowledge_base(**arguments)
        context = "\n\n".join(results) if results else "No relevant information found."
        
        messages.append(message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": context
        })
        
        final_response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS
        )
        return final_response.choices[0].message.content
        
    return message.content