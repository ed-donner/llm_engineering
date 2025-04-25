# Let's start by making a useful function

ticket_prices = {"london": "$799", "paris": "$899", "tokyo": "$1400", "berlin": "$499"}

def get_ticket_price(destination_city):
    print(f"Tool get_ticket_price called for {destination_city}")
    city = destination_city.lower()
    return ticket_prices.get(city, "Unknown")

def make_a_booking(destination_city, customer_name, customer_id):
    print(f"Tool make_a_booking called for {destination_city}")
    city = destination_city.lower()
    print(f"Customer name: {customer_name}, Customer ID: {customer_id}")
    return True

# There's a particular dictionary structure that's required to describe our function:

price_function = {
    "name": "get_ticket_price",
    "description": "Get the price of a return ticket to the destination city. Call this whenever you need to know the ticket price, for example when a customer asks 'How much is a ticket to this city'",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False
    }
}

booking_function = {
    "name": "make_a_booking",
    "description": "Make a booking for a customer to a destination city. Call this when a customer wants to book a flight. You can get the customer's name and ID by directly asking the customer. For example, you can say 'What is your name?' or 'What is your ID?'",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
            "customer_name": {
                "type": "string",
                "description": "The name of the customer making the booking",
            },
            "customer_id": {
                "type": "string",
                "description": "The unique identifier for the customer",
            }
        },
        "required": ["destination_city", "customer_name", "customer_id"],
        "additionalProperties": False
    }
}

