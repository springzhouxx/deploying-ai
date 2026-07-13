from langchain.tools import tool
import requests

from utils.logger import get_logger

_logs = get_logger(__name__)

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather codes -> short human description
_WEATHER_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    61: "slight rain", 63: "moderate rain", 65: "heavy rain",
    71: "slight snow fall", 73: "moderate snow fall", 75: "heavy snow fall",
    80: "slight rain showers", 81: "moderate rain showers", 82: "violent rain showers",
    95: "thunderstorm", 96: "thunderstorm with slight hail", 99: "thunderstorm with heavy hail",
}


@tool
def get_atmosphere_report(city: str) -> str:
    """
    Fetches the current weather for a city using the free Open-Meteo API
    (no API key required). Returns raw structured data: temperature (C),
    wind speed (km/h), humidity (%), and a short condition description.
    Use this to set the mood for the on-air atmosphere report; do not read
    this raw data to the listener verbatim, rephrase it as part of the show.
    """
    _logs.debug(f"Looking up weather for city: {city}")
    location = _geocode(city)
    if location is None:
        return f"Could not find a location named '{city}'."

    forecast = _fetch_forecast(location["latitude"], location["longitude"])
    current = forecast.get("current", {})
    condition = _WEATHER_CODES.get(current.get("weather_code"), "unknown conditions")

    report = (
        f"City: {location['name']}, {location.get('country', '')}\n"
        f"Condition: {condition}\n"
        f"Temperature: {current.get('temperature_2m')} C\n"
        f"Humidity: {current.get('relative_humidity_2m')}%\n"
        f"Wind speed: {current.get('wind_speed_10m')} km/h"
    )
    _logs.debug(f"Atmosphere report: {report}")
    return report


def _geocode(city: str) -> dict | None:
    response = requests.get(GEOCODE_URL, params={"name": city, "count": 1})
    response.raise_for_status()
    results = response.json().get("results")
    if not results:
        return None
    return results[0]


def _fetch_forecast(latitude: float, longitude: float) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m,weather_code,relative_humidity_2m",
    }
    response = requests.get(FORECAST_URL, params=params)
    response.raise_for_status()
    return response.json()
