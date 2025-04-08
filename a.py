"""ZMQ-based log aggregation server.

Collects and stores logs from distributed components.
"""
import zmq
from loguru import logger

logger.add("logs/unified.log", rotation="00:00", compression="zip")


def main() -> None:
    """Start the log server to listen for incoming log messages on port 9999."""
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.bind("tcp://*:9999")

    logger.info("Log server started. Listening on port 9999...")

    try:
        while True:
            message = socket.recv_string()
            logger.info(message)
    except zmq.ZMQError:
        logger.exception("ZMQ error while receiving or logging message")
    except KeyboardInterrupt:
        logger.info("Log server shutdown via KeyboardInterrupt.")
    finally:
        socket.close()
        context.term()