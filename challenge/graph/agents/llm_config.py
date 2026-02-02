from challenge_inferencia.settings import LLM_API_KEY, LLM_MODEL_NAME
from langchain_openai import ChatOpenAI

def get_llm() -> ChatOpenAI:
    """    
    Returns the appropriate LLM based on available API keys.
    Raises an error if no API key is found.
    It uses OpenAI's ChatOpenAI model with specified parameters.
    """
    if LLM_API_KEY is not None:
        return ChatOpenAI(
            model=LLM_MODEL_NAME,
            temperature=0,
            api_key=LLM_API_KEY
        )
    else:
        raise ValueError(
            "No API key found. "
            "Configure LLM_API_KEY in the .env file."
        )