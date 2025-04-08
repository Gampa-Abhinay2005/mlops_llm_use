import logging
from datetime import date

import folium
import requests
import streamlit as st
from streamlit_folium import folium_static

from llm import ask_travel_assistant

# Setup logging
logging.basicConfig(
    filename="travel_assistant.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

st.set_page_config(page_title="AI Travel Assistant", layout="centered")
st.title("🌍 AI Travel Assistant")

# --- AI Assistant Section ---
user_input = st.text_input("Ask me anything about your trip:")
if st.button("Ask AI"):
    logging.info(f"User asked AI: {user_input}")
    try:
        response = ask_travel_assistant(user_input)
        logging.info("AI response generated successfully.")
        st.write("🤖 AI Response:", response)
    except Exception as e:
        logging.exception(f"AI response error: {e}")
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
}

for key in ["selected_city", "show_weather", "show_hotels", "show_attractions", "show_map"]:
    if key not in st.session_state:
        st.session_state[key] = False if "show" in key else ""

dest_display = st.selectbox("Select your destination city:", list(airport_codes.keys()))
dest_code = airport_codes[dest_display]
if st.button("Confirm Selection"):
    st.session_state.selected_city = dest_display
    logging.info(f"Destination selected: {dest_display} ({dest_code})")

if st.session_state.selected_city:
    selected_city_display = st.session_state.selected_city
    selected_city_code = airport_codes[selected_city_display]

    if st.button("🌤️ Show Weather"):
        st.session_state.show_weather = True
        logging.info("User requested weather info.")

    if st.session_state.show_weather:
        try:
            weather_resp = requests.get(f"http://127.0.0.1:8000/weather?city={selected_city_code}").json()
            if "main" in weather_resp:
                logging.info(f"Weather data fetched for {selected_city_display}")
                st.write(f"🌡️ **Weather in {selected_city_display}:** {weather_resp['main']['temp']}°C")
                st.write(f"☁️ **Conditions:** {weather_resp['weather'][0]['description']}")
                st.write(f"💧 **Humidity:** {weather_resp['main']['humidity']}%")
            else:
                logging.warning(f"Weather data not available for {selected_city_display}")
                st.warning("Weather data not available.")
        except Exception as e:
            logging.exception(f"Weather fetch error for {selected_city_display}: {e}")
            st.error(f"Weather fetch error: {e}")

    st.header("🎯 Tourist Attractions")
    attraction_city = st.text_input("Enter a city to explore its top attractions:")
    if st.button("Get Attractions"):
        logging.info(f"User requested attractions in: {attraction_city}")
        try:
            res = requests.get(f"http://127.0.0.1:8000/attractions/?city={attraction_city}")
            data = res.json()
            if "attractions" in data:
                logging.info(f"Attractions fetched for {attraction_city}")
                st.write(f"Top places to visit in {attraction_city}:")
                for place in data["attractions"]:
                    st.markdown(f"✅ {place}")
            else:
                logging.warning(f"No attractions found for {attraction_city}")
                st.warning("No attractions found.")
        except Exception as e:
            logging.exception(f"Error fetching attractions for {attraction_city}: {e}")
            st.error(f"Error fetching attractions: {e}")

    st.subheader("✈️ Flight Search")
    source_display = st.selectbox("Select your departure city:", list(airport_codes.keys()))
    source_code = airport_codes[source_display]
    travel_date = st.date_input("Select travel date:", date.today())

    if st.button("Search Flights"):
        logging.info(f"Searching flights: from {source_display} to {selected_city_display} on {travel_date}")
        with st.spinner("Searching for flights..."):
            try:
                flights_resp = requests.get(
                    f"http://127.0.0.1:8000/dummy/flights?from_code={source_code}&to_code={selected_city_code}&date={travel_date}",
                ).json()

                if isinstance(flights_resp, list) and flights_resp:
                    logging.info(f"{len(flights_resp)} flights found from {source_display} to {selected_city_display}")
                    st.success(f"Found {len(flights_resp)} flights from {source_display} to {selected_city_display}")
                    for flight in flights_resp:
                        st.write(f"""
                        **{flight['airline']}**  
                        ✈️ Flight: {flight['flight']}  
                        💰 Price: {flight['price']}  
                        🕒 Departure: {flight['departure']}  
                        🕔 Arrival: {flight['arrival']}  
                        ---  
                        """)
                else:
                    logging.warning("No flights found.")
                    st.warning("No flights found for this route.")
            except Exception as e:
                logging.exception(f"Flight fetch error: {e}")
                st.error(f"Flight fetch error: {e}")

    if st.button("🏨 Show Hotels"):
        st.session_state.show_hotels = True
        logging.info(f"User requested hotels in {selected_city_display}")

    if st.session_state.show_hotels:
        try:
            hotels_resp = requests.get(f"http://127.0.0.1:8000/dummy/hotels?city={selected_city_code}").json()
            hotels = hotels_resp.get("data", [])
            if hotels:
                logging.info(f"{len(hotels)} hotels found in {selected_city_display}")
                for hotel in hotels:
                    st.write(f"🏨 **{hotel['name']}** – 💰 Price: {hotel['price']}")
            else:
                logging.warning(f"No hotels found for {selected_city_display}")
                st.warning("No hotels available.")
        except Exception as e:
            logging.exception(f"Hotel fetch error: {e}")
            st.error(f"Hotel fetch error: {e}")

    if st.button("🗺️ Show on Map"):
        st.session_state.show_map = True
        logging.info(f"User requested map for {selected_city_display}")

    if st.session_state.show_map:
        try:
            coord_resp = requests.get(f"http://127.0.0.1:8000/map?city={selected_city_display}").json()
            lat, lon = coord_resp.get("lat"), coord_resp.get("lon")
            if lat and lon:
                logging.info(f"Coordinates found for {selected_city_display}: ({lat}, {lon})")
                m = folium.Map(location=[lat, lon], zoom_start=12)
                folium.Marker([lat, lon], popup=selected_city_display).add_to(m)
                folium_static(m)
            else:
                logging.warning(f"Could not locate {selected_city_display} on map")
                st.warning("Could not locate city on map.")
        except Exception as e:
            logging.exception(f"Map fetch error: {e}")
            st.error(f"Map fetch error: {e}")
