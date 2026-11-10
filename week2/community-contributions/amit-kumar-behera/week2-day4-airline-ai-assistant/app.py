import json
import os

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

from flight_service import book_flight, search_flights
from tools import tools


load_dotenv()

MODEL = "gpt-4.1-mini"

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


SYSTEM_MESSAGE = """
You are FlightAI, a specialized airline assistant.

You are strictly focused on flight and airline-related tasks.

You may help with:
- Searching for flights
- Flight schedules and status
- Departure and arrival information
- Flight duration
- Airline information related to flights
- Simulated flight bookings

When a user asks to find flights:
- Identify the departure and destination locations.
- Use the search_flights tool.
- Present the returned flight information clearly.
- Never invent flight information.
- If no flights are found, tell the user clearly.

When a user wants to book a flight:
- Ask for the passenger's name if it has not been provided.
- Make sure the user has selected a flight.
- Identify the source and destination from the conversation.
- Use the book_flight tool only when the passenger name, flight number,
  source, and destination are known.
- The booking tool verifies that the flight exists on the requested route.
- Clearly tell the user that the booking is simulated and does not create
  a real reservation or process payment.

Do not answer unrelated questions such as:
- Programming or coding problems
- Mathematics
- General knowledge
- Writing requests
- Unrelated technical questions

For unrelated requests, politely explain that you are a flight and
airline assistant and can only help with flight-related tasks.

Be friendly, concise, and accurate.
"""


def execute_tool(tool_call):
    """Execute a tool requested by the model."""

    tool_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)

    if tool_name == "search_flights":
        return search_flights(
            arguments["source"],
            arguments["destination"],
        )

    if tool_name == "book_flight":
        return book_flight(
            flight_number=arguments["flight_number"],
            passenger_name=arguments["passenger_name"],
            source=arguments["source"],
            destination=arguments["destination"],
        )

    return {
        "error": f"Unknown tool: {tool_name}"
    }


def build_messages(message, history):
    """Build OpenAI messages from the Gradio conversation history."""

    messages = [
        {
            "role": "system",
            "content": SYSTEM_MESSAGE,
        }
    ]

    for item in history:
        if isinstance(item, dict):
            messages.append(item)

        elif isinstance(item, (list, tuple)) and len(item) == 2:
            user_message, assistant_message = item

            if user_message:
                messages.append(
                    {
                        "role": "user",
                        "content": user_message,
                    }
                )

            if assistant_message:
                messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_message,
                    }
                )

    messages.append(
        {
            "role": "user",
            "content": message,
        }
    )

    return messages


def chat(message, history):
    """Run the FlightAI conversation."""

    messages = build_messages(message, history)

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message

        # The model has finished and does not need a tool.
        if not assistant_message.tool_calls:
            return assistant_message.content

        # Add the model's tool request to the conversation.
        messages.append(
            assistant_message.model_dump(
                exclude_none=True
            )
        )

        # Execute each requested tool.
        for tool_call in assistant_message.tool_calls:
            tool_result = execute_tool(tool_call)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result),
                }
            )


demo = gr.ChatInterface(
    fn=chat,
    title="✈️ FlightAI",
    description=(
        "AI-powered airline assistant for flight search, "
        "flight information, and simulated bookings."
    ),
    examples=[
        "Find flights from Delhi to Mumbai",
        "Show me flights from Mumbai to Delhi",
        "Are there flights from Bengaluru to Hyderabad?",
        "Book a flight from Delhi to Mumbai",
    ],
)


if __name__ == "__main__":
    demo.launch()