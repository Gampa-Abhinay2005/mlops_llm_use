from langchain.llms import Ollama
from loguru import logger

from logging_client import setup_logger

setup_logger()

llm = Ollama(
    model="llama3",
    temperature=0.7,
    top_p=0.95,
    top_k=40,
    repeat_penalty=1.1,
    num_predict=256,
)

def ask_travel_assistant(question: str):
    try:
        logger.info(f"Received question: {question}")
        response = llm.invoke(question)
        logger.info(f"Response: {response}")
        return response
    except Exception:
        logger.exception("Error while invoking travel assistant")
        return "Sorry, an error occurred while processing your request."
