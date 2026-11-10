flight_search_tool = {
    "type": "function",
    "function": {
        "name": "search_flights",
        "description": (
            "Search for operating flights between two locations. "
            "The locations can be city names, airport names, or IATA codes."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Departure city, airport, or IATA code.",
                },
                "destination": {
                    "type": "string",
                    "description": "Arrival city, airport, or IATA code.",
                },
            },
            "required": ["source", "destination"],
            "additionalProperties": False,
        },
    },
}


book_flight_tool = {
    "type": "function",
    "function": {
        "name": "book_flight",
        "description": (
            "Create a simulated booking for a flight. "
            "The flight must exist between the specified source and "
            "destination. This does not make a real reservation "
            "or process payment."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "flight_number": {
                    "type": "string",
                    "description": "Flight number, such as AI441.",
                },
                "passenger_name": {
                    "type": "string",
                    "description": "Name of the passenger.",
                },
                "source": {
                    "type": "string",
                    "description": "Departure city, airport, or IATA code.",
                },
                "destination": {
                    "type": "string",
                    "description": "Arrival city, airport, or IATA code.",
                },
            },
            "required": [
                "flight_number",
                "passenger_name",
                "source",
                "destination",
            ],
            "additionalProperties": False,
        },
    },
}


tools = [
    flight_search_tool,
    book_flight_tool,
]