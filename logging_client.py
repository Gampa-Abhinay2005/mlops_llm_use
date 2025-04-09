"""Logging client module to load configuration and setup local + remote logging via ZeroMQ."""

from typing import Any

import toml
import zmq
from loguru import logger


def load_config(config_path: str = "logging_config.toml") -> dict[str, Any]:
    """Load the logging configuration from a TOML file.

    Args:
        config_path : Path to the TOML config file. Defaults to 'logging_config.toml'.

    Returns:
        dict: Logging configuration dictionary from the [logging] section.

    """
    try:
        config = toml.load(config_path)
        return config.get("logging", {})
    except Exception as e:
        logger.error(f"Failed to load config file {config_path}: {e}")
        raise


def setup_logger(config_path: str = "logging_config.toml") -> None:
    """Set up the logger with local file logging and remote ZeroMQ forwarding.

    Args:
        config_path: Path to the TOML config file. Defaults to 'logging_config.toml'.

    """
    config = load_config(config_path)

    logger.remove()

    log_file_name = config.get("log_file_name", "default.log")
    min_log_level = config.get("min_log_level", "INFO")
    log_rotation = config.get("log_rotation", "1 week")
    log_compression = config.get("log_compression", "zip")
    logging_server_port_no = config.get("logging_server_port_no", 9000)

    logger.add(
        log_file_name,
        level=min_log_level,
        rotation=log_rotation,
        compression=log_compression,
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    logger.info(
        f"Logger set up: File - {log_file_name}, Level - {min_log_level}, "
        f"Rotation - {log_rotation}, Compression - {log_compression}",
    )

    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect(f"tcp://localhost:{logging_server_port_no}")

    def zmq_forward(message: str) -> None:
        """Forward a log message to a ZeroMQ socket.

        Args:
            message (str): Log message to forward.

        """
        try:
            socket.send_string(message)
        except Exception as e:
            logger.error(f"Failed to forward message via ZMQ: {e}")
    class ZMQSink:
        def write(self, message: str) -> None:
            if message.strip():
                zmq_forward(message)
        def flush(self) -> None:
            pass
    # Add ZMQ sink for remote logging
    logger.add(ZMQSink(), level=min_log_level)

    logger.info("Remote logging (ZMQ) set up successfully.")

