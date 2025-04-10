"""
Module for interacting with the AI Travel Assistant.

Uses the Ollama language model with LangChain agent tools to handle natural language queries,
fetching data from your FastAPI endpoints for weather, hotels, flights, and attractions.
"""

import httpx
import requests
from langchain_ollama import OllamaLLM
from langchain_core.exceptions import OutputParserException
from langchain.agents import initialize_agent, Tool, AgentType
from loguru import logger
from logging_client import setup_logger

setup_logger()

# Initialize the LLM with your model and parameters
llm = OllamaLLM(
    model="llama3",
    temperature=0.3,
    top_p=0.95,
    top_k=40,
    repeat_penalty=1.1,
    num_predict=100,
)

# -------------------------------
# Functions to fetch data from FastAPI endpoints

def fetch_weather(city: str) -> str:
    """Fetch current weather data from the FastAPI endpoint."""
    try:
        response = requests.get(f"http://127.0.0.1:8000/weather?city={city}", timeout=5)
        data = response.json()
        if "main" in data:
            temp = data["main"]["temp"]
            condition = data["weather"][0]["description"]
            return f"Weather in {city}: {temp}°C, {condition}."
        else:
            return f"Weather data not available for {city}."
    except Exception as e:
        return f"Error fetching weather: {e}"

def fetch_hotels(city: str) -> str:
    """Fetch dummy hotel data from the FastAPI endpoint."""
    try:
        response = requests.get(f"http://127.0.0.1:8000/dummy/hotels?city={city}", timeout=5)
        data = response.json()
        if "data" in data and data["data"]:
            hotels = data["data"]
            hotels_list = ", ".join([f"{h['name']} ({h['price']})" for h in hotels])
            return f"Hotels in {city}: {hotels_list}."
        else:
            return f"No hotels available for {city}."
    except Exception as e:
        return f"Error fetching hotels: {e}"

def fetch_flights(query: str) -> str:
    """Fetch dummy flight data from the FastAPI endpoint.
    
    Expected input format: "from_city to to_city"
    """
    try:
        parts = [s.strip() for s in query.split(" to ")]
        if len(parts) != 2:
            return "Please provide flight query in the format 'from_city to to_city'."
        from_city, to_city = parts
        response = requests.get(
            f"http://127.0.0.1:8000/dummy/flights?from_code={from_city}&to_code={to_city}",
            timeout=5,
        )
        data = response.json()
        if isinstance(data, list) and data:
            flights_str = ""
            for flight in data:
                flights_str += (
                    f"{flight['airline']} flight {flight['flight']} departs at {flight['departure']} "
                    f"and arrives at {flight['arrival']}. Price: {flight['price']}\n"
                )
            return flights_str.strip()
        else:
            return f"No flights found from {from_city} to {to_city}."
    except Exception as e:
        return f"Error fetching flights: {e}"

def fetch_attractions(city: str) -> str:
    """Fetch attractions data from the FastAPI endpoint."""
    try:
        response = requests.get(f"http://127.0.0.1:8000/attractions/?city={city}", timeout=5)
        data = response.json()
        if "attractions" in data and data["attractions"]:
            attractions_list = ", ".join(data["attractions"])
            return f"Attractions in {city}: {attractions_list}."
        else:
            return f"No attractions found for {city}."
    except Exception as e:
        return f"Error fetching attractions: {e}"

# -------------------------------
# Define LangChain Tools to connect these functions

tools = [
    Tool.from_function(
        func=fetch_weather,
        name="Weather",
        description="Get current weather for a city. Input should be the city name."
    ),
    Tool.from_function(
        func=fetch_hotels,
        name="Hotels",
        description="Get available hotels in a city. Input should be the city name."
    ),
    Tool.from_function(
        func=fetch_flights,
        name="Flights",
        description="Get flight information. Input should be in the format 'from_city to to_city'."
    ),
    Tool.from_function(
        func=fetch_attractions,
        name="Attractions",
        description="Get tourist attractions in a city. Input should be the city name."
    ),
]

# Create the agent with the tools and LLM
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)


def ask_travel_assistant(question: str) -> str:
    """Process a user question using the LLM-based travel assistant with integrated tools.

    If the question contains keywords related to travel data, the agent will use the tools
    to fetch real data from your APIs. Otherwise, it falls back to a direct LLM response.
    """
    try:
        logger.info(f"Received question: {question}")
        keywords = ["weather", "hotel", "flight", "attraction", "attractions"]
        if any(word in question.lower() for word in keywords):
            response = agent.run(question)
        else:
            response = llm.invoke(question)
        logger.info(f"Response: {response}")
        return response
    except (httpx.RequestError, OutputParserException) as e:
        logger.exception("Error while invoking travel assistant")
        return "Sorry, an error occurred while processing your request."