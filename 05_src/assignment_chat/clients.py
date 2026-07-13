import os

from langchain_openai import ChatOpenAI
from chromadb.utils.embedding_functions.openai_embedding_function import OpenAIEmbeddingFunction

USE_GATEWAY = os.getenv("USE_GATEWAY", "FALSE").upper() == "TRUE"
GATEWAY_BASE_URL = "https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1"


def get_chat_model(model: str = "gpt-4o-mini", use_gateway: bool = USE_GATEWAY) -> ChatOpenAI:
    """
    Returns a ChatOpenAI model, routed through the API gateway
    when USE_GATEWAY is true instead of a OPENAI_API_KEY.
    """
    if use_gateway:
        return ChatOpenAI(
            model=model,
            base_url=GATEWAY_BASE_URL,
            api_key="any value",
            default_headers={"x-api-key": os.getenv("API_GATEWAY_KEY")},
        )
    return ChatOpenAI(model=model)


def get_embedding_function(
    model: str = "text-embedding-3-small", use_gateway: bool = USE_GATEWAY
) -> OpenAIEmbeddingFunction:
    """
    Returns a Chroma-compatible embedding function, routed through the API gateway 
    when USE_GATEWAY is true, so queries land in the same embedding space 
    as the precomputed vectors stored in the vector db.
    """
    if use_gateway:
        return OpenAIEmbeddingFunction(
            model_name=model,
            api_base=GATEWAY_BASE_URL,
            api_key="any value",
            default_headers={"x-api-key": os.getenv("API_GATEWAY_KEY")},
        )
    return OpenAIEmbeddingFunction(model_name=model, api_key=os.getenv("OPENAI_API_KEY"))
