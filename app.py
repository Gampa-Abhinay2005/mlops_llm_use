import streamlit as st
import requests
# from streamlit_folium import folium_static
from llm import ask_travel_assistant  # Import AI assistant function

st.title("🌍 AI Travel Assistant")

# User input for AI assistance
user_input = st.text_input("Ask me anything about your trip:")

if st.button("Ask AI"):
    response = ask_travel_assistant(user_input)
    st.write("🤖 AI Response:", response)

st.header("✈️ Travel Info")

city = st.text_input("Enter a city:")

if st.button("Get Travel Info"):
    # Get Weather
    weather_resp = requests.get(f"http://127.0.0.1:8000/weather?city={city}").json()
    if "main" in weather_resp:
        st.write(f"🌤️ **Weather in {city}:** {weather_resp['main']['temp']}°C")

    # Get Flights
    flights_resp = requests.get(f"http://127.0.0.1:8000/flights?city={city}").json()
    if flights_resp:
        st.write("✈️ **Available Flights:**")
        for flight in flights_resp:
            st.write(f"• {flight['airline']} - {flight['flight']} - {flight['price']}")

    # Get Hotels
    hotels_resp = requests.get(f"http://127.0.0.1:8000/hotels?city={city}").json()
    if hotels_resp:
        st.write("🏨 **Available Hotels:**")
        for hotel in hotels_resp:
            st.write(f"• {hotel['name']} - {hotel['price']}")

    # Get Attractions
    attractions_resp = requests.get(f"http://127.0.0.1:8000/attractions?city={city}").json()
    if attractions_resp:
        st.write("🏛️ **Top Attractions:**")
        for attraction in attractions_resp:
            st.write(f"• {attraction['name']} - {attraction['description']}")

    # Get Map
    map_resp = requests.get(f"http://127.0.0.1:8000/map?city={city}")
    if map_resp.status_code == 200:
        st.components.v1.html(map_resp.text, height=500)
    else:
        st.error("City not found!")
