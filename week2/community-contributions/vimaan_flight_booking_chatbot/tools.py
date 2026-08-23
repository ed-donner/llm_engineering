import requests
import os
import random
from helpers import location_formatting, parse_flight_offers, update_passengers_table, update_bookings_table 


booking_api_key = os.getenv('RAPID_API_KEY')


def get_ticket_price(source_city, destination_city, adult_count, date_of_journey, children_ages=None):

    if adult_count <= 0:
        raise ValueError("At least one adult must be present")

    if not source_city or not destination_city:
        raise ValueError("Source and destination cannot be empty")

    print("Fetching ticket prices...")

    url = "https://booking-com15.p.rapidapi.com/api/v1/flights/searchFlights"

    headers = {
        "x-rapidapi-key": booking_api_key,
        "x-rapidapi-host": "booking-com15.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    children_str = ""
    children_str = ",".join(map(str, children_ages)) if children_ages else ""
    querystring = {
        "fromId": location_formatting(source_city),
        "toId": location_formatting(destination_city),
        "departDate": date_of_journey,
        "stops": "none",
        "pageNo": "1",
        "adults": str(adult_count),
        "children": children_str,
        "sort": "BEST",
        "cabinClass": "ECONOMY",
        "currency_code": "INR"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code}, {response.text}")

    print("Ticket Prices Fetched. Starting Parsing...")
    return parse_flight_offers(response.json())


def book_flight(passengers, flight_number, flight_company, doj):
    passenger_ids = update_passengers_table(passengers)
    pnr_number = update_bookings_table(passenger_ids, flight_number, flight_company, doj)
    return pnr_number