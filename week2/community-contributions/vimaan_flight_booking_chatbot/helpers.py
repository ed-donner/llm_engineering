import random
import sqlite3
import string


def location_formatting(iata_code):
    return f"{iata_code}.AIRPORT"


def parse_flight_offers(data):
    flights = []

    for offer in data.get("data", {}).get("flightOffers", []):

        segments = offer.get("segments", [])
        if not segments:
            continue

        segment = segments[0]

        # Airline
        try:
            airline = segment["legs"][0]["carriersData"][0]["name"]
            flight_number = segment["legs"][0]["flightInfo"]["flightNumber"]
        except (KeyError, IndexError):
            airline = "Unknown"
            flight_number = None

        # Price
        price = offer.get("priceBreakdown", {}).get("total", {}).get("units")

        # Times
        departure = segment.get("departureTime")
        arrival = segment.get("arrivalTime")

        # Airports
        departure_airport = segment.get("departureAirport", {}).get("code")
        arrival_airport = segment.get("arrivalAirport", {}).get("code")

        # Duration
        duration_sec = segment.get("totalTime")
        duration_min = duration_sec // 60 if duration_sec else None

        # Stops
        stops = len(segment.get("legs", [])) - 1

        flights.append({
            "airline": airline,
            "flight_number": flight_number,
            "price": price,
            "departure": departure,
            "arrival": arrival,
            "departure_airport": departure_airport,
            "arrival_airport": arrival_airport,
            "duration_minutes": duration_min,
            "stops": stops
        })

    print(f"{len(flights)} flights fetched.")
    return flights


def update_passengers_table(passengers):
    print("Updating Passengers Table... Please wait.")
    conn = sqlite3.connect("vimaan.db")
    cursor = conn.cursor()
    passenger_ids = []
    for passenger in passengers:
        passenger_first_name = passenger["first_name"]
        passenger_middle_name = passenger.get("middle_name", "")
        passenger_last_name = passenger["last_name"]
        passenger_age = passenger["age"]
        records = cursor.execute("""SELECT passenger_id FROM passengers where first_name = ? and middle_name = ? and last_name = ? and age = ?;""", (passenger_first_name, passenger_middle_name, passenger_last_name, passenger_age))
        record = records.fetchone()
        if record:
            passenger_ids.append(record[0])
            continue
        else:
            cursor.execute("INSERT INTO passengers (first_name, middle_name, last_name, age) VALUES (?, ?, ?, ?)", (passenger_first_name, passenger_middle_name, passenger_last_name, passenger_age))
            passenger_ids.append(cursor.lastrowid)
    conn.commit()
    conn.close()
    print("Passengers Table Updated Successfully.")
    return passenger_ids


def generate_pnr():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))


def update_bookings_table(passenger_ids, flight_number, flight_company, datetime_of_journey):
    print("Updating Bookings Table... Please wait.")
    pnr_number = generate_pnr()
    conn = sqlite3.connect("vimaan.db")
    cursor = conn.cursor()
    for passenger_id in passenger_ids:
        print(datetime_of_journey)
        cursor.execute("INSERT INTO bookings (pnr_number, passenger_id, flight_number, flight_company, datetime_of_journey) VALUES (?, ?, ?, ?, ?)", (pnr_number, passenger_id, flight_number, flight_company, datetime_of_journey))
    conn.commit()
    conn.close()
    print("Bookings Table Updated Successfully.")
    return pnr_number