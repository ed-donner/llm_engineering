import os
import random
import string

import requests
from dotenv import load_dotenv

from airport_service import get_iata_code


load_dotenv()

AIRLABS_API_KEY = os.getenv("AIRLABS_API_KEY")
AIRLABS_URL = "https://airlabs.co/api/v9/schedules"


def search_flights(source, destination):
    """Search operating flights between two locations."""

    source_iata = get_iata_code(source)
    destination_iata = get_iata_code(destination)

    if not source_iata:
        return {
            "error": f"I couldn't find an airport for '{source}'."
        }

    if not destination_iata:
        return {
            "error": f"I couldn't find an airport for '{destination}'."
        }

    try:
        response = requests.get(
            AIRLABS_URL,
            params={
                "api_key": AIRLABS_API_KEY,
                "dep_iata": source_iata,
                "arr_iata": destination_iata,
            },
            timeout=10,
        )

        response.raise_for_status()

    except requests.RequestException:
        return {
            "error": (
                "I couldn't retrieve flight information right now. "
                "Please try again later."
            )
        }

    data = response.json()

    flights = []

    for flight in data.get("response", []):
        # Ignore codeshare entries.
        if flight.get("cs_flight_iata"):
            continue

        flights.append(
            {
                "flight_number": flight.get("flight_iata"),
                "departure": flight.get("dep_time"),
                "arrival": flight.get("arr_time"),
                "status": flight.get("status"),
                "duration_minutes": flight.get("duration"),
            }
        )

    if not flights:
        return {
            "source": source_iata,
            "destination": destination_iata,
            "flights": [],
            "message": (
                f"No operating flights were found from "
                f"{source_iata} to {destination_iata}."
            ),
        }

    return {
        "source": source_iata,
        "destination": destination_iata,
        "flights": flights,
    }


def book_flight(
    flight_number,
    passenger_name,
    source,
    destination,
):
    """Verify a flight and create a simulated booking."""

    if not passenger_name or not passenger_name.strip():
        return {
            "error": "Please provide the passenger's name."
        }

    if not flight_number or not flight_number.strip():
        return {
            "error": "Please provide a flight number."
        }

    # Verify that the flight actually exists on this route.
    search_result = search_flights(source, destination)

    if "error" in search_result:
        return search_result

    selected_flight = next(
        (
            flight
            for flight in search_result["flights"]
            if flight["flight_number"]
            and flight["flight_number"].upper()
            == flight_number.strip().upper()
        ),
        None,
    )

    if not selected_flight:
        return {
            "error": (
                f"Flight {flight_number.strip().upper()} was not found "
                f"from {search_result['source']} to "
                f"{search_result['destination']}."
            )
        }

    booking_reference = "".join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=6,
        )
    )

    return {
        "status": "confirmed",
        "booking_reference": booking_reference,
        "passenger_name": passenger_name.strip(),
        "flight": selected_flight,
        "source": search_result["source"],
        "destination": search_result["destination"],
        "message": (
            "This is a simulated booking. "
            "No real reservation or payment was made."
        ),
    }