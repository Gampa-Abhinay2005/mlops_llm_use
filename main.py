"""Main FastAPI app for the AI Travel Assistant.

Includes endpoints for weather, flights, hotels, and tourist attractions using
various external APIs.
"""
from __future__ import annotations

import os
from http import HTTPStatus
from pathlib import Path
from typing import Any

import httpx
import requests
import toml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from geopy.geocoders import Nominatim
from loguru import logger

# --- Load Loguru config from TOML ---
config = toml.load("logging_config.toml")

log_file = config.get("log_file_name", "logs/server.log")
Path(log_file).parent.mkdir(parents=True, exist_ok=True)

logger.remove()  # Remove default stderr logger
logger.add(
    log_file,
    level=config.get("min_log_level", "INFO"),
    rotation=config.get("log_rotation", "10 MB"),
    compression=config.get("log_compression", "zip"),
    backtrace=True,
    diagnose=True,
    enqueue=True,
)
# -------------------------------------

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "1eabd2a5eb938cd031880dcd7904fa45")
GEOAPIFY_API_KEY = "f1253c87d2554289834ca1d3b3382c1e"

@app.get("/weather")
async def get_weather(city: str) -> dict[str, Any]:
    """Fetch current weather for a given city using OpenWeather API."""
    logger.info(f"Fetching weather for city: {city}")

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={WEATHER_API_KEY}&units=metric"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)

        if response.status_code == HTTPStatus.OK:
            logger.info(f"Weather data fetched successfully for city: {city}")
            return response.json()

        logger.error(
            f"Failed to fetch weather data for city: {city}, "
            f"Status Code: {response.status_code}",
        )
        return {"error": "Failed to fetch weather data"}

    except httpx.RequestError as e:
        logger.error(f"Request error while fetching weather data: {e}")
        return {"error": "Request to weather API failed"}

DUMMY_DATA = {
    "flights": {
        "LHR-DEL": [
            {
                "airline": "British Airways",
                "flight": "BA257",
                "price": "₹42,500",
                "departure": "2025-04-07T08:15:00",
                "arrival": "2025-04-07T22:30:00",
            },
            {
                "airline": "Air India",
                "flight": "AI161",
                "price": "₹38,900",
                "departure": "2025-04-07T13:45:00",
                "arrival": "2025-04-08T03:20:00",
            },
        ],
        "JFK-LHR": [
            {
                "airline": "Virgin Atlantic",
                "flight": "VS138",
                "price": "$850",
                "departure": "2025-04-07T18:30:00",
                "arrival": "2025-04-08T06:45:00",
            },
        ],
        "DEL-BOM": [
            {
                "airline": "IndiGo",
                "flight": "6E531",
                "price": "₹4,200",
                "departure": "2025-04-07T07:00:00",
                "arrival": "2025-04-07T09:15:00",
            },
            {
                "airline": "Vistara",
                "flight": "UK927",
                "price": "₹5,800",
                "departure": "2025-04-07T12:30:00",
                "arrival": "2025-04-07T14:45:00",
            },
        ],
    },
    "hotels": {
        "DELHI": [
            {"name": "The Leela Palace New Delhi", "price": "₹12,500/night"},
            {"name": "Taj Mahal Hotel", "price": "₹9,800/night"},
            {"name": "ITC Maurya", "price": "₹11,200/night"},
        ],
        "DEL": [
            {"name": "The Leela Palace New Delhi", "price": "₹12,500/night"},
            {"name": "Taj Mahal Hotel", "price": "₹9,800/night"},
            {"name": "ITC Maurya", "price": "₹11,200/night"},
        ],
        "LHR": [
            {"name": "The Ritz London", "price": "£450/night"},
            {"name": "Park Plaza Westminster Bridge", "price": "£220/night"},
        ],
        "JFK": [
            {"name": "The Plaza Hotel", "price": "$650/night"},
            {"name": "Marriott Marquis", "price": "$320/night"},
        ],
        "BOM": [
            {"name": "Taj Lands End", "price": "₹15,000/night"},
            {"name": "The St. Regis Mumbai", "price": "₹18,500/night"},
        ],
    },
}

@app.get("/dummy/flights")
async def get_dummy_flights(from_code: str, to_code: str):
    """Retrieve dummy flight data for a given route and date."""
    route = f"{from_code}-{to_code}"
    logger.info(f"Fetching dummy flights for route: {route} ")
    if route in DUMMY_DATA["flights"]:
        logger.info(f"Flights found for route: {route}")
        return DUMMY_DATA["flights"][route]
    logger.warning(f"No dummy flights available for route: {route}")
    return {"message": "No dummy flights available for this route"}

@app.get("/dummy/hotels")
async def get_dummy_hotels(city: str) ->dict:
    """Retrieve dummy hotel data for a given city."""
    logger.info(f"Fetching dummy hotels for city: {city}")
    if city in DUMMY_DATA["hotels"]:
        logger.info(f"Hotels found for city: {city}")
        return {"data": DUMMY_DATA["hotels"][city]}
    logger.warning(f"No dummy hotels available for city: {city}")
    return {"message": "No dummy hotels available for this city"}

def get_coordinates(city: str) -> tuple[float, float] | None:
    """Get the latitude and longitude of a city using the Nominatim geocoder.

    Args:
        city (str): The name of the city to geocode.

    Returns:
        Optional[tuple[float, float]]: Latitude and longitude as a tuple,
        or None if not found.

    """
    logger.info(f"Fetching coordinates for city: {city}")
    geolocator = Nominatim(user_agent="travel_app")
    location = geolocator.geocode(city)
    if location:
        logger.info(
        f"Coordinates for {city}: ({location.latitude}, {location.longitude})",
        )

    else:
        logger.error(f"Could not find coordinates for city: {city}")
    return (location.latitude, location.longitude) if location else (None, None)

@app.get("/attractions/")
def get_attractions(city: str) -> dict[str, list[str] | str]:
    """Get top 10 tourist attractions for a given city using Geoapify.

    Args:
        city (str): The name of the city to search for attractions.

    Returns:
        dict: A dictionary containing a list of attraction names or an error message.

    """
    logger.info(f"Fetching attractions for city: {city}")
    try:
        url = f"https://api.geoapify.com/v1/geocode/search?text={city}&apiKey={GEOAPIFY_API_KEY}"
        geo_response = requests.get(url, timeout=10)
        geo_response.raise_for_status()
        geo_data = geo_response.json()

        if geo_data["features"]:
            lat = geo_data["features"][0]["properties"]["lat"]
            lon = geo_data["features"][0]["properties"]["lon"]
            logger.info(f"City coordinates: ({lat}, {lon})")

            places_url = (
                f"https://api.geoapify.com/v2/places?"
                f"categories=tourism.attraction&filter=circle:{lon},{lat},5000"
                f"&limit=10&apiKey={GEOAPIFY_API_KEY}"
            )
            places_resp = requests.get(places_url, timeout=10)
            places_resp.raise_for_status()
            places_data = places_resp.json()

            attractions = [
                place["properties"]["name"]
                for place in places_data.get("features", [])
                if place["properties"].get("name")
            ]

            logger.info(f"Found {len(attractions)} attractions in {city}")
            return {"attractions": attractions}
        logger.warning(f"City not found in Geoapify: {city}")
        return {"error": "City not found"}
    except requests.RequestException as e:
        logger.exception("Network-related error occurred while fetching attractions")
        return {"error": str(e)}



@app.get("/map")
async def get_map(city: str) -> dict[str, float]:
    """Get geographic coordinates for a specified city.

    Args:
        city (str): The name of the city.

    Returns:
        dict: A dictionary with latitude and longitude of the city.

    """
    logger.info(f"Fetching map coordinates for city: {city}")
    lat, lon = get_coordinates(city)
    if lat is None:
        logger.error(f"Map: City not found: {city}")
        return {"error": "City not found"}
    logger.info(f"Map coordinates for {city}: lat={lat}, lon={lon}")
    return {"lat": lat, "lon": lon}
