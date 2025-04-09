# 🌍 Smart Travel Planner - Production Justfile
set shell := ["bash", "-ce"]
set dotenv-load

# --- Configuration ---
venv := ".venv_travel"
ollama_model := "llama3"
log_dir := "logs"

# --- Setup Commands ---
setup:
    uv venv --python=python3.11 {{venv}}
    source {{venv}}/bin/activate && cd mlops_llm_use && uv pip install -r requirements.txt
    ollama pull {{ollama_model}}
    mkdir -p {{log_dir}}

# --- Run All Services ---
run:
    cd mlops_llm_use && \
    source {{venv}}/bin/activate && \
    uvicorn main:app --reload & \
    uv run streamlit run app.py

clean:
    echo "🧹 Cleaning environment..."
    rm -rf {{venv}} {{log_dir}} .pytest_cache __pycache__ .mypy_cache
    echo "✅ Project cleaned"
