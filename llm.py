"""LangChain-Ollama Agent for AI Travel Assistant.

Fetches weather, hotel, flight, and attraction info from FastAPI endpoints,
and responds to natural language queries using Ollama LLM.
"""

from __future__ import annotations

import httpx
import requests
from langchain.agents import AgentType, Tool, initialize_agent
from langchain_core.exceptions import OutputParserException
from langchain_ollama import OllamaLLM
from loguru import logger

from logging_client import setup_logger

setup_logger()

MAX_FLIGHT_PARTS = 2

# Initialize the LLM
llm = OllamaLLM(
    model="llama3",
    temperature=0.3,
    top_p=0.95,
    top_k=40,
    repeat_penalty=1.1,
)

# -------------------------------
# FastAPI Fetch Functions

def fetch_weather(city: str) -> str:
    """Fetch weather from FastAPI endpoint."""
    try:
        resp = requests.get(
            f"http://127.0.0.1:8000/weather?city={city}", timeout=5,
        )
        data = resp.json()
        if "main" in data:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            return f"Weather in {city}: {temp}°C, {desc}."
        return f"Weather data not available for {city}."
    except requests.RequestException as err:
        return f"Error fetching weather: {err}"

def fetch_hotels(city: str) -> str:
    """Fetch hotels from FastAPI endpoint."""
    try:
        code = city.strip().upper()
        resp = requests.get(
            f"http://127.0.0.1:8000/dummy/hotels?city={code}", timeout=5,
        )
        data = resp.json()
        if data.get("data"):
            hotels = data["data"]
            summary = ", ".join(
                f"{h['name']} ({h['price']})" for h in hotels
            )
            return f"Hotels in {code}: {summary}."
        return f"[END] No hotels found in {code}."
    except requests.RequestException as err:
        return f"Error fetching hotels: {err}"

def fetch_flights(query: str) -> str:
    """Fetch flights from FastAPI endpoint.

    Input should be in 'FROM to TO' format.
    """
    try:
        query = query.strip("'\"")  # <- Strip quotes around the string
        parts = [s.strip().upper() for s in query.split(" to ")]
        if len(parts) != 2:
            return (
                "Please provide flight query in the format "
                "'from_code to to_code'. Example: DEL to BOM."
            )

        from_code, to_code = parts
        url = (
            f"http://127.0.0.1:8000/dummy/flights?"
            f"from_code={from_code}&to_code={to_code}"
        )
        response = requests.get(url, timeout=5)
        data = response.json()

        if isinstance(data, list) and data:
            flights_str = ""
            for flight in data:
                flights_str += (
                    f"{flight['airline']} flight {flight['flight']} departs at "
                    f"{flight['departure']} and arrives at {flight['arrival']}. "
                    f"Price: {flight['price']}\n"
                )
            return flights_str.strip()

        return f"No flights found from {from_code} to {to_code}."
    except requests.RequestException as err:
        return f"Error fetching flights: {err}"

def fetch_attractions(city: str) -> str:
    """Fetch tourist attractions from FastAPI endpoint."""
    try:
        resp = requests.get(
            f"http://127.0.0.1:8000/attractions/?city={city}", timeout=5,
        )
        data = resp.json()
        if data.get("attractions"):
            places = ", ".join(data["attractions"])
            return f"Attractions in {city}: {places}."
        return f"No attractions found for {city}."
    except requests.RequestException as err:
        return f"Error fetching attractions: {err}"

# -------------------------------
# Tool Definitions and Matching

tools = [
    Tool.from_function(
        func=fetch_weather,
        name="Weather",
        description="Get current weather for a city. Input = city name.",
    ),
    Tool.from_function(
        func=fetch_hotels,
        name="Hotels",
        description="Get hotels in a city. Input = city name.",
    ),
    Tool.from_function(
        func=fetch_flights,
        name="Flights",
        description=(
            "Get flights between cities. Input = 'FROM to TO', "
            "e.g., 'DEL to BOM'."
        ),
    ),
    Tool.from_function(
        func=fetch_attractions,
        name="Attractions",
        description="Get tourist attractions. Input = city name.",
    ),
]

TOOL_KEYWORDS = {
    "Weather": ["weather", "climate", "temperature"],
    "Hotels": ["hotel", "hotels", "stay", "lodging", "accommodation"],
    "Flights": ["flight", "flights", "airline", "depart", "arrival", "plane"],
    "Attractions": [
        "attractions", "places", "sightseeing", "spots", "visit",
        "monuments", "tourist",
    ],
}

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    return_intermediate_steps=True,
    max_iterations=2,
)

def detect_tool(question: str) -> str | None:
    """Detect tool based on fuzzy keyword matching."""
    q = question.lower()
    for name, kws in TOOL_KEYWORDS.items():
        if any(kw in q for kw in kws):
            return name
    return None

# -------------------------------
# Core Travel Assistant Logic

def ask_travel_assistant(question: str) -> str:
    """Answer travel questions using LLM and LangChain tools."""
    try:
        logger.info(f"Question: {question}")
        tool = detect_tool(question)

        if tool:
            result = agent.invoke({"input": question}, return_intermediate_steps=True)
            steps = result.get("intermediate_steps", [])
            if steps:
                action, observation = steps[0]
                logger.info(f"Used: {action.tool}, Observation: {observation}")
                return observation
            return result.get("output", "Sorry, no result found.")

        reply = llm.invoke(question)
        logger.info(f"LLM Reply: {reply}")
        return reply

    except (httpx.RequestError, OutputParserException, Exception):
        logger.exception("Error in travel assistant.")
        return "Sorry, something went wrong answering your query."
