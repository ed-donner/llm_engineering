from amadeus import Client, Location, ResponseError

def filter_other_countries(airports):
    country_codes_wights = {}
    for airport in airports:
        country_code = airport["address"]["countryCode"]
        country_codes_wights[country_code] = country_codes_wights.get(country_code, 0) + 1
    country_code = max(country_codes_wights, key=country_codes_wights.get)
    return [airport for airport in airports if airport["address"]["countryCode"] == country_code]


class TravelAPI:
    def __init__(self, client_id, client_secret):
        self.client = Client(client_id=client_id, client_secret=client_secret)
        
    def get_airport(self, search):
        try:
            airport_locations = self.client.reference_data.locations.get(
                keyword=search,
                subType=Location.AIRPORT,
            )
            return filter_other_countries(airport_locations.data)
        except ResponseError as e:
            print(f"Amadeus API ResponseError in get_airport: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error in get_airport: {e}")
            return []
    
    def get_city(self, search, country_code="IT"):
        try:
            city_locations = self.client.reference_data.locations.get(
                keyword=search,
                subType=Location.CITY,
                countryCode=country_code
            )
            return city_locations.data
        except ResponseError as e:
            print(f"Amadeus API ResponseError in get_city: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error in get_city: {e}")
            return []
    
    def get_flight(self, origin_location_code, destination_location_code, departure_date, adults=1):
        try:
            offers = self.client.shopping.flight_offers_search.get(
                originLocationCode=origin_location_code,
                destinationLocationCode=destination_location_code,
                departureDate=departure_date,
                adults=adults)
            return offers.data
        except ResponseError as e:
            print(f"Amadeus API ResponseError in get_flight: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error in get_flight: {e}")
            return []