# importing necessary libraries and defining constants for the geocoding and weather APIs, as well as a mapping of weather codes to descriptions. The main function get_weather takes a city name, geocodes it to get coordinates, fetches the current weather data for those coordinates, and returns a structured result as a dictionary.
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

import requests


_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# https://open-meteo.com/en/docs (WMO weather interpretation codes)
_WEATHER_CODE_DESCRIPTION: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


@dataclass(frozen=True)
class WeatherResult:
    # implementing as a dataclass for convenience, immutability, and easy conversion to dict for JSON serialization
    city: str
    country: Optional[str]
    latitude: float
    longitude: float
    timezone: Optional[str]
    observed_at: Optional[str]
    temperature_c: Optional[float]
    apparent_temperature_c: Optional[float]
    relative_humidity_pct: Optional[float]
    wind_speed_kph: Optional[float]
    precipitation_mm: Optional[float]
    weather_code: Optional[int]
    weather_description: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _geocode_city(city: str, timeout_s: float = 15.0) -> Dict[str, Any]:
    # Helper function to geocode a city name to coordinates using the Open-Meteo geocoding API. Returns the first result or raises an error if not found.
    resp = requests.get(
        _GEOCODE_URL,
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=timeout_s,
    )
    resp.raise_for_status()
    data = resp.json() or {}
    results = data.get("results") or []
    if not results:
        raise ValueError(f"Could not find coordinates for city: {city!r}")
    return results[0]


def get_weather(city: str, timeout_s: float = 20.0) -> Dict[str, Any]:
    """
    Fetch current weather for a given city using the free Open-Meteo APIs.

    Returns a JSON-serializable dict suitable for passing back as a tool result.
    """
    city = (city or "").strip()
    if not city:
        raise ValueError("city must be a non-empty string")

    geo = _geocode_city(city, timeout_s=timeout_s)
    lat = float(geo["latitude"])
    lon = float(geo["longitude"])

    resp = requests.get(
        _FORECAST_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": ",".join(
                [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "precipitation",
                    "weather_code",
                    "wind_speed_10m",
                ]
            ),
            "timezone": "auto",
        },
        timeout=timeout_s,
    )
    resp.raise_for_status()
    data = resp.json() or {}
    current = data.get("current") or {}

    code = current.get("weather_code")
    code_int = int(code) if code is not None else None
    desc = _WEATHER_CODE_DESCRIPTION.get(code_int) if code_int is not None else None

    result = WeatherResult(
        city=str(geo.get("name") or city),
        country=geo.get("country"),
        latitude=lat,
        longitude=lon,
        timezone=data.get("timezone"),
        observed_at=current.get("time"),
        temperature_c=current.get("temperature_2m"),
        apparent_temperature_c=current.get("apparent_temperature"),
        relative_humidity_pct=current.get("relative_humidity_2m"),
        wind_speed_kph=current.get("wind_speed_10m"),
        precipitation_mm=current.get("precipitation"),
        weather_code=code_int,
        weather_description=desc,
    )
    return result.to_dict()


# print(get_weather("Nairobi"))

