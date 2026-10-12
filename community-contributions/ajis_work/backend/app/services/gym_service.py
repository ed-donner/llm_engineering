import httpx

from app.core.config import settings


async def find_nearby_gyms(
    latitude: float,
    longitude: float,
    radius: int = 3000,
):
    url = "https://places.googleapis.com/v1/places:searchNearby"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": settings.GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": (
            "places.id,"
            "places.displayName,"
            "places.formattedAddress,"
            "places.location,"
            "places.rating,"
            "places.userRatingCount,"
            "places.regularOpeningHours,"
            "places.websiteUri"
        ),
    }

    body = {
        "includedTypes": ["gym"],
        "maxResultCount": 10,
        "rankPreference": "DISTANCE",
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius": radius,
            }
        },
    }

    # DEBUG: don't print the actual API key
    print("API key exists:", bool(headers.get("X-Goog-Api-Key")))
    print("API key length:", len(headers.get("X-Goog-Api-Key", "")))
    print("Headers being sent:", list(headers.keys()))

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            json=body,
        )

        print("STATUS:", response.status_code)
        print("GOOGLE RESPONSE:", response.text)

        if response.status_code != 200:
            return {
                "google_status": response.status_code,
                "google_response": response.json(),
            }

        return response.json()