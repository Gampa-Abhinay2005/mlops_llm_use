
import toml
import zmq
from loguru import logger


def load_config(config_path="logging_config.toml"):
    return toml.load(config_path)

def setup_logger(config_path="logging_config.toml"):
    config = load_config(config_path)
    logger.remove()

    # Set up local log file writing
    logger.add(
        config["log_file_name"],
        level=config["min_log_level"],
        rotation=config["log_rotation"],
        compression=config["log_compression"],
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    # Forward to remote log server
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect("tcp://localhost:9999")

    def zmq_forward(message):
        try:
            socket.send_string(message)
        except Exception:
            pass

    class ZMQSink:
        def write(self, message):
            if message.strip():
                zmq_forward(message)
        def flush(self):
            pass

    logger.add(ZMQSink(), level=config["min_log_level"])

