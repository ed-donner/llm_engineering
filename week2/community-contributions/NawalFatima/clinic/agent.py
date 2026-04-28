# imports

"""
agent.py — LLM Agent and Tool Orchestration

This module contains the core agent logic for the clinic booking assistant.
It manages the conversation flow, calls the appropriate tools based on LLM decisions,
and returns responses to the Gradio UI.

Components:
- get_system_message(): Builds the system prompt with the current date and time,
  and the step-by-step booking flow instructions for the LLM.

- handle_tool_calls(): Receives tool call requests from the LLM, routes them to
  the correct database or email function, and returns results back to the LLM.
  All tool calls and results are logged for debugging.

- chat(): The main conversation function. Builds the message history, calls the LLM,
  runs the tool call loop until the LLM produces a final response, and returns the reply.
  Handles errors gracefully and retries on tool_use_failed errors.

Model: GPT-4.1 Mini via OpenAI library
"""
import sys
print(sys.path)
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
from tools import tools
from db_tools import get_specialist_info, get_availability_slots, book_appointment, get_all_specialties
from email_utils import send_confirmation_email

import logging

logging.basicConfig(
    filename="clinic_agent.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    print(f"OPENAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OPENAI API Key not set")
    
OPENAIMODEL = "gpt-4.1-mini"
openai = OpenAI()






def get_system_message():
    now = datetime.now()
    current_date = now.strftime("%A, %d %B %Y")
    current_time = now.strftime("%H:%M")
    
    return f"""You are a clinic appointment booking assistant for Family Wellness Clinic.
    IMPORTANT: When you need to use a tool, call it as a proper function call only. Never write tool calls inline in your text response.
    Current date: {current_date}. Current time: {current_time}.

    Greet the user ONCE at the start with "Welcome to Family Wellness Clinic! How may I help you today?"

    BOOKING FLOW - follow these steps in exact order:
    1. Ask for the patient's name and reason for visit.
    2. Call get_specialist_info ONCE to find doctors for the relevant specialty.
    3. Present the doctors and ask which one they prefer.
    4. Call get_availability_slots ONCE with the chosen doctor's name.
    5. Display ALL available slots to the user clearly before asking them to choose.
    6. Ask the user to pick a slot.
    7. Ask for their email and phone number.
    8. Once the details are complete, call book_appointment immediately with all collected details 
    9. If book_appointment returns a message starting with "Appointment booked:", the booking succeeded. Call send_confirmation_email immediately.
    10. Confirm the booking to the user with a friendly summary.

    STRICT RULES:
    - Send exactly ONE message per turn. Stop and wait for the user to reply.
    - Never call the same tool twice in the same conversation turn.
    - Never ask for a preferred time before showing available slots.
    - Never simulate future dialogue or write (Waiting for user input).
    - Never second-guess a successful booking. If you see "Appointment booked:", proceed to email.
    - Pass day_of_week exactly as shown in slots e.g. "Monday" not "monday".
    - Pass time in HH:MM format exactly e.g. "09:00" not "9am" or "09.00".
    - Never expose slot IDs, SQL, or internal logic to the user.
    - DO NOT hallucinate slot times or doctor names.
    """




def handle_tool_calls(message):
    responses = []

    for tool_call in message.tool_calls:
        func_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        safe_args = {k: "***" if k in ("patient_email", "patient_phone") else v 
             for k, v in arguments.items()}
        logging.info(f"Tool called: {func_name} with args: {safe_args}")

        try:
            if func_name == "get_specialist_info":
                result = get_specialist_info(arguments.get("specialty"))

            elif func_name == "get_all_specialties":
                result = get_all_specialties()

            elif func_name == "get_availability_slots":
                result = get_availability_slots(arguments.get("doctor_name"))

            elif func_name == "book_appointment":
                result = book_appointment(
                    arguments.get("patient_name"),
                    arguments.get("patient_email"),
                    arguments.get("patient_phone"),
                    arguments.get("doctor_name"),
                    arguments.get("day_of_week"),
                    arguments.get("time"),
                    arguments.get("reason")
                )

            elif func_name == "send_confirmation_email":
                result = send_confirmation_email(
                    arguments.get("patient_email"),
                    arguments.get("patient_name"),
                    arguments.get("doctor_name"),
                    arguments.get("day_of_week"),
                    arguments.get("time"),
                    arguments.get("reason")
                )

            else:
                result = f"Unknown tool: {func_name}"

            logging.info(f"Tool result for {func_name}: {result}")

        except Exception as e:
            logging.exception(f"Tool {func_name} failed: {e}")
            result = f"Error executing {func_name}: {e}"

        responses.append({
            "role": "tool",
            "content": result,
            "tool_call_id": tool_call.id
        })

    return responses




def chat(message, history):
    try:
        history = [{"role": h["role"], "content": h["content"]} for h in history]
        messages = [{"role": "system", "content": get_system_message()}] + history + [{"role": "user", "content": message}]
        logging.info(f"User message: {message}")
        
        try:
            response = openai.chat.completions.create(model=OPENAIMODEL, messages=messages, tools=tools)
        except Exception as e:
            if "tool_use_failed" in str(e):
                logging.warning("Tool use failed on first attempt, retrying...")
                response = openai.chat.completions.create(model=OPENAIMODEL, messages=messages, tools=tools)
            else:
                raise

        while response.choices[0].finish_reason == "tool_calls":
            tool_message = response.choices[0].message
            responses = handle_tool_calls(tool_message)
            messages.append({
                "role": "assistant",
                "content": tool_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in tool_message.tool_calls
                ]
            })
            messages.extend(responses)
            try:
                response = openai.chat.completions.create(model=OPENAIMODEL, messages=messages, tools=tools)
            except Exception as e:
                if "tool_use_failed" in str(e):
                    logging.warning("Tool use failed, retrying...")
                    response = openai.chat.completions.create(model=OPENAIMODEL, messages=messages, tools=tools)
                else:
                    raise

        reply = response.choices[0].message.content
        logging.info(f"Assistant reply: {reply}")
        return reply

    except Exception as e:
        logging.error(f"Chat failed: {e}")
        return "I'm sorry, something went wrong. Please try again."