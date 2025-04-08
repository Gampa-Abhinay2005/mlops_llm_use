import os

import toml
import yaml


def load_configs():
    log_config = toml.load("logging_config.toml")
    fastapi_config = toml.load("fastapi_config.toml")
    with open("app_config.yaml") as f:
        app_config = yaml.safe_load(f)

    os.environ["WEATHER_API_KEY"] = app_config["weather_api"]["key"]
    os.environ["GEOAPIFY_API_KEY"] = app_config["geoapify"]["key"]

    return log_config, fastapi_config, app_config
