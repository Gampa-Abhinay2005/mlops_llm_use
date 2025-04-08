"""Configuration loader module.

Loads logging, FastAPI, and application-level configurations.
Sets environment variables based on loaded values.
"""


import os
from pathlib import Path

import toml
import yaml


def load_configs() -> tuple[dict, dict, dict]:
    """Load all configuration files and set relevant environment variables.

    Returns:
        Tuple[dict, dict, dict]:
            - log_config: Dictionary from logging_config.toml
            - fastapi_config: Dictionary from fastapi_config.toml
            - app_config: Dictionary from app_config.yaml


    """
    log_config = toml.load(Path("logging_config.toml"))
    fastapi_config = toml.load(Path("fastapi_config.toml"))

    with Path("app_config.yaml").open(encoding="utf-8") as f:
        app_config = yaml.safe_load(f)

    os.environ["WEATHER_API_KEY"] = app_config["weather_api"]["key"]
    os.environ["RAPIDAPI_KEY"] = app_config["rapidapi"]["key"]
    os.environ["GEOAPIFY_API_KEY"] = app_config["geoapify"]["key"]

    return log_config, fastapi_config, app_config