"""Streamlit app for an AI-powered travel assistant.

This app provides weather, hotel, attraction, and flight search
functionality using various APIs and a chatbot interface.
"""

import logging

import folium
import requests
import streamlit as st
from streamlit_folium import folium_static

from llm import ask_travel_assistant

logger = logging.getLogger(__name__)


# Setup logging
logging.basicConfig(
    filename="travel_assistant.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

st.set_page_config(page_title="AI Travel Assistant", layout="centered")
st.title("AI Travel Assistant")

# --- AI Assistant Section ---
user_input = st.text_input("Ask me anything about your trip:")
if st.button("Ask AI"):
    logger.info("User asked AI: %s", user_input)
    try:
        response = ask_travel_assistant(user_input)
        logger.info("AI response generated successfully.")
        st.write("🤖 AI Response:", response)
    except Exception:
        logger.exception("AI response error")
        st.error("Something went wrong while getting AI response.")

# --- Travel Info Section ---
st.header("✈️ Travel Info")

airport_codes = {
    "London (Heathrow - LHR)": "LHR",
    "New York (JFK)": "JFK",
    "Delhi (DEL)": "DEL",
    "Paris (CDG)": "CDG",
    "Tokyo (Haneda - HND)": "HND",
    "San Francisco (SFO)": "SFO",
    "Dubai (DXB)": "DXB",
    "Mumbai (BOM)": "BOM",
    "Sydney (SYD)": "SYD",
    "Los Angeles (LAX)": "LAX",
    "palakkad (PGD)": "Palakkad",
    "Kochi (COK)": "Kochi",
}

for key in [
    "selected_city",
    "show_weather",
    "show_hotels",
    "show_attractions",
    "show_map",
]:
    if key not in st.session_state:
        st.session_state[key] = False if "show" in key else ""

dest_display = st.selectbox("Select your destination city:", list(airport_codes.keys()))
dest_code = airport_codes[dest_display]
if st.button("Confirm Selection"):
    st.session_state.selected_city = dest_display
    logger.info("Destination selected: %s (%s)", dest_display, dest_code)

if st.session_state.selected_city:
    selected_city_display = st.session_state.selected_city
    selected_city_code = airport_codes[selected_city_display]

    if st.button("🌤️ Show Weather"):
        st.session_state.show_weather = True
        logger.info("User requested weather info.")

    if st.session_state.show_weather:
        try:
            weather_resp = requests.get(f"http://127.0.0.1:8000/weather?city={selected_city_code}",timeout=5).json()
            if "main" in weather_resp:
                logger.info("Weather data fetched for %s", selected_city_display)
                temp = weather_resp["main"]["temp"]
                st.write(f"🌡️ *Weather in {selected_city_display}:* {temp}°C")
                condition = weather_resp["weather"][0]["description"]
                st.write(f"☁️ *Conditions:* {condition}")
                st.write(f"💧 *Humidity:* {weather_resp['main']['humidity']}%")
            else:
                logger.warning("No weather data for %s", selected_city_display)
                st.warning("Weather data not available.")
        except Exception as e:
            logger.exception("Weather fetch error: %s", selected_city_display)
            st.error(f"Weather fetch error: {e}")

    st.header("🎯 Tourist Attractions")
    attraction_city = st.text_input("Enter a city to explore its top attractions:")
    if st.button("Get Attractions"):
        logger.info("User requested attractions in: %s", attraction_city)
        try:
            res = requests.get(f"http://127.0.0.1:8000/attractions/?city={attraction_city}",timeout=5)
            data = res.json()
            if "attractions" in data:
                logger.info("Attractions fetched for %s", attraction_city)
                st.write(f"Top places to visit in {attraction_city}:")
                for place in data["attractions"]:
                    st.markdown(f"✅ {place}")
            else:
                logger.warning("No attractions found for %s", attraction_city)
                st.warning("No attractions found.")
        except Exception as e:
            logger.exception("Error fetching attractions for %s", attraction_city)
            st.error(f"Error fetching attractions: {e}")

    st.subheader("✈️ Flight Search")
    cities = list(airport_codes.keys())
    source_display = st.selectbox("Select your departure city:", cities)
    source_code = airport_codes[source_display]
    if st.button("Search Flights"):
        with st.spinner("Searching for flights..."):
            try:
                flights_resp = requests.get(
                    f"http://127.0.0.1:8000/dummy/flights?from_code={source_code}&to_code={selected_city_code}",
                timeout=5).json()

                if isinstance(flights_resp, list) and flights_resp:
                    logger.info(
                        "%d flights found from %s to %s",
                        len(flights_resp), source_display, selected_city_display,
                    )
                    st.success(
                        f"Found {len(flights_resp)} flights from {source_display} "
                        f"to {selected_city_display}",
                    )
                    for flight in flights_resp:
                        st.write(f"""
                        *{flight['airline']}*
                        ✈️ Flight: {flight['flight']}
                        💰 Price: {flight['price']}
                        🕒 Departure: {flight['departure']}
                        🕔 Arrival: {flight['arrival']}
                        ---
                        """)
                else:
                    logger.warning("No flights found.")
                    st.warning("No flights found for this route.")
            except Exception as e:
                logger.exception("Flight fetch error")
                st.error(f"Flight fetch error: {e}")

    if st.button("🏨 Show Hotels"):
        st.session_state.show_hotels = True
        logger.info("User requested hotels in %s", selected_city_display)

    if st.session_state.show_hotels:
        try:
            hotels_resp = requests.get(f"http://127.0.0.1:8000/dummy/hotels?city={selected_city_code}",timeout=5).json()
            hotels = hotels_resp.get("data", [])
            if hotels:
                logger.info("%d hotels found in %s", len(hotels), selected_city_display)
                for hotel in hotels:
                    st.write(f"🏨 *{hotel['name']}* - 💰 Price: {hotel['price']}")
            else:
                logger.warning("No hotels found for %s", selected_city_display)
                st.warning("No hotels available.")
        except Exception as e:
            logger.exception("Hotel fetch error")
            st.error(f"Hotel fetch error: {e}")

    if st.button("🗺️ Show on Map"):
        st.session_state.show_map = True
        logger.info("User requested map for %s", selected_city_display)

    if st.session_state.show_map:
        try:
            coord_resp = requests.get(
                f"http://127.0.0.1:8000/map?city={selected_city_display}",
                timeout=5,
            ).json()

            lat, lon = coord_resp.get("lat"), coord_resp.get("lon")
            if lat and lon:
                logger.info(
                    "Coordinates found for %s: (%s, %s)",
                    selected_city_display,
                    lat,
                    lon,
                )

                m = folium.Map(location=[lat, lon], zoom_start=12)
                folium.Marker([lat, lon], popup=selected_city_display).add_to(m)
                folium_static(m)
            else:
                logger.warning("Could not locate %s on map", selected_city_display)
                st.warning("Could not locate city on map.")
        except requests.RequestException:
            logger.exception("Map fetch error")
            st.error("Map fetch error occured")
