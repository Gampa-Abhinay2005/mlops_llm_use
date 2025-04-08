import toml
import zmq
from loguru import logger

def load_config(config_path="logging_config.toml"):
    try:
        config = toml.load(config_path)
        # Access the [logging] section of the config
        return config.get("logging", {})
    except Exception as e:
        logger.error(f"Failed to load config file {config_path}: {e}")
        raise

def setup_logger(config_path="logging_config.toml"):
    config = load_config(config_path)
    
    # Remove the default logger configuration
    logger.remove()

    # Get the logging configurations with fallback default values
    log_file_name = config.get("log_file_name", "default.log")  # Fallback to "default.log"
    min_log_level = config.get("min_log_level", "INFO")  # Default to "INFO"
    log_rotation = config.get("log_rotation", "1 week")  # Default to rotate logs weekly
    log_compression = config.get("log_compression", "zip")  # Default to "zip"
    logging_server_port_no = config.get("logging_server_port_no", 9000)  # Default to port 9000

    # Set up local log file writing
    logger.add(
        log_file_name,
        level=min_log_level,
        rotation=log_rotation,
        compression=log_compression,
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    logger.info(f"Logger set up: File - {log_file_name}, Level - {min_log_level}, Rotation - {log_rotation}, Compression - {log_compression}")

    # Forward to remote log server using ZeroMQ
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect(f"tcp://localhost:{logging_server_port_no}")  # Use the configured port

    def zmq_forward(message):
        try:
            socket.send_string(message)
        except Exception as e:
            logger.error(f"Failed to forward message via ZMQ: {e}")

    class ZMQSink:
        def write(self, message):
            if message.strip():
                zmq_forward(message)

        def flush(self):
            pass

    # Add ZMQ sink for remote logging
    logger.add(ZMQSink(), level=min_log_level)

    logger.info("Remote logging (ZMQ) set up successfully.")

