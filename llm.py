from langchain.llms import Ollama

llm = Ollama(model="llama3")

def ask_travel_assistant(question: str):
    response = llm.invoke(question)
    return response
