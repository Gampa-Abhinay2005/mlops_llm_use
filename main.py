from fastapi import FastAPI
from pydantic import BaseModel
import requests
import folium
from geopy.geocoders import Nominatim

app = FastAPI()

WEATHER_API_KEY = "your_openweather_api_key"

class TravelRequest(BaseModel):
    city: str

# Get weather information
@app.get("/weather")
async def get_weather(city: str):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    return response.json()

# Dummy flight data
flights_db = {
    "Paris": [{"flight": "AF123", "price": "$400", "airline": "Air France"}],
    "NYC": [{"flight": "DL456", "price": "$500", "airline": "Delta"}]
}

@app.get("/flights")
async def get_flights(city: str):
    return flights_db.get(city, [])

# Dummy hotel data
hotels_db = {
    "Paris": [{"name": "Hotel Eiffel", "price": "$200"}],
    "NYC": [{"name": "Times Square Hotel", "price": "$250"}]
}

@app.get("/hotels")
async def get_hotels(city: str):
    return hotels_db.get(city, [])

# Dummy attractions data
attractions_db = {
    "Paris": [{"name": "Eiffel Tower", "description": "Famous landmark in Paris."}],
    "NYC": [{"name": "Statue of Liberty", "description": "Iconic American symbol."}]
}

@app.get("/")
def home():
    return {"message": "Hello, FastAPI!"}
@app.get("/attractions")
async def get_attractions(city: str):
    return attractions_db.get(city, [])

# Get coordinates for a city
def get_coordinates(city: str):
    geolocator = Nominatim(user_agent="travel_app")
    location = geolocator.geocode(city)
    return (location.latitude, location.longitude) if location else (None, None)

# Generate a map for a city
@app.get("/map")
async def get_map(city: str):
    lat, lon = get_coordinates(city)
    if lat is None:
        return {"error": "City not found"}

    m = folium.Map(location=[lat, lon], zoom_start=12)
    folium.Marker([lat, lon], popup=city, icon=folium.Icon(color="red")).add_to(m)
    return m._repr_html_()
