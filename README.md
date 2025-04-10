# 🧠 Smart AI Travel Assistant

This is an AI-powered Travel Assistant that uses LangChain and Ollama (LLaMA 3) to answer travel-related queries such as:

- 🧳 Weather forecasts
- 🏨 Hotels in a city
- ✈️ Available flights between cities
- 📍 Top attractions

It integrates a FastAPI backend, Streamlit frontend, centralized logging using Loguru + ZeroMQ, and LLM-powered natural language processing.

---

## ✨ Features

- 🔍 Natural Language Travel Queries via LangChain + LLaMA 3
- ⚙️ FastAPI Endpoints for Weather, Flights, Hotels, and Attractions
- 🌐 Streamlit Frontend with Interactive Maps (Folium)
- 📜 Configurable via `TOML` and `YAML`
- 🪵 Centralized Logging via `logging_server.py`
- ⚡ Justfile automation for setup and running

---

## 🚀 How to Run
just setup
just run

use these commands to run

### 1. Clone the repo

```bash
git clone https://github.com/your-username/mlops_llm_use.git
cd mlops_llm_use
