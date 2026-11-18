# go and get your weapons from db.py and use them here to make your agent more powerful
from db import get_ticket_price, set_ticket_price, book_ticket

price_card = {
    "name": "get_ticket_price",
    "description": "Get the price of return flight to the destination city.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "The city the customer wants to travel to."},
        },
        "required": ["city"],
        "additionalProperties": False
    }
}
set_price_card = {
    "name": "set_ticket_price",
    "description": "Set the price of a return flight to a specific city.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "The city the customer wants to travel to."},
            "price": {"type": "number", "description": "The price of the return flight."},
        },
        "required": ["city", "price"],
        "additionalProperties": False
    }
}   
book_card = {
    "name": "book_ticket",
    "description": "Book a return flight to a specific city for the passenger",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "The name of the passenger."},
            "city": {"type": "string", "description": "The city the customer wants to travel to."}
        },
        "required": ["name", "city"],
        "additionalProperties": False
    }
}
tool_cards = [{"type": "function", "function": price_card}, {"type": "function", "function": set_price_card}, {"type": "function", "function": book_card}]

tool_functions = {"get_ticket_price": get_ticket_price, "set_ticket_price": set_ticket_price, "book_ticket": book_ticket}