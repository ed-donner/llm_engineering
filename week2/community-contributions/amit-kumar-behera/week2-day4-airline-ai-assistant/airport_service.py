import airportsdata

airports = airportsdata.load("IATA")


def get_iata_code(location):
    """Convert a city, airport name, or IATA code to an IATA code."""
    location = location.strip()

    # Already an IATA code
    if location.upper() in airports:
        return location.upper()

    location_lower = location.lower()

    for iata, airport in airports.items():
        if (
            airport["city"].lower() == location_lower
            or airport["name"].lower() == location_lower
            or airport["subd"].lower() == location_lower
        ):
            return iata

    return None