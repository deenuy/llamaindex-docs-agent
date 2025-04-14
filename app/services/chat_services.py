"""
services/chat_service.py

This module handles the business logic for processing chat messages.
It bridges the API layer and the agent, and supports streamed and synchronous responses.
"""

from typing import Generator
import requests
import os
from dotenv import load_dotenv
from app.agents.react_agent import initialize_react_agent, initialize_web_search_tool
from app.retrieval_engine.router_engine import initialize_router_tool
from app.retrieval_engine.summary_engine import initialize_summary_engine
from app.retrieval_engine.vector_search_engine import initialize_vector_engine
from app.utils.config.config_loader import ConfigLoader
from app.clients.tavily import get_tavily_client
from app.utils.logger.logger import setup_logger
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

# Initialize logger
logger = setup_logger()

# Load environment and config
env = os.getenv("ENVIRONMENT", "dev")
logger.info(f"Environment set to: {env}")

# Load configuration
config_loader = ConfigLoader(env=env)
config = config_loader.load_config()

# Initialize qdrant client
qc = QdrantClient(
    url=f"http://localhost:{config['qdrant']['service']['http_port']}",
    prefer_grpc=False
)


def initialize_services(env: str = "dev"):
    """
    Initializes services and dependencies.

    Args:
        env (str): Environment name (default: "dev").

    Returns:
        tuple: (agent instance, config dictionary)
    """

    # ✅ Initialize vector engine (missing in your current code)
    vector_engine = initialize_vector_engine(config, qdrant_client=qc)

    # ✅ Initialize summary engine
    summary_engine = initialize_summary_engine(config)

    # ✅ Pass vector engine to router tool
    router_tool = initialize_router_tool(summary_engine, vector_engine)

    # ✅ Initialize web search tool
    web_search_tool = initialize_web_search_tool()

    # Initialize agent
    agent = initialize_react_agent(router_tool, web_search_tool)

    logger.info("✅ Services initialized successfully.")
    return agent, config

def process_message(agent, message: str) -> str:
    """
    Processes a message synchronously through the agent.

    Args:
        agent: The initialized ReAct agent instance.
        message (str): User message.

    Returns:
        str: Agent response.
    """
    logger.info(f"Processing message: {message}")
    response = agent.chat(message)
    return str(response)

def stream_reply(message: str, history: list = None) -> Generator[str, None, None]:
    """
    Streams the response for Gradio interface.

    Args:
        message (str): User input message.
        history (list, optional): Chat history (not used currently).

    Yields:
        str: Streamed response character by character.
    """
    if not message:
        yield "You should provide me with a message."
    else:
        try:
            response = requests.post(
                "http://localhost:8000/message",
                json={"message": message}
            )
            response.raise_for_status()
            reply_message = response.json().get("message", "")
            logger.info(f"Streaming response: {reply_message}")

            accumulated = ""
            for char in reply_message:
                accumulated += char
                yield accumulated

        except requests.RequestException as e:
            logger.error(f"Error during streaming reply: {e}")
            yield "⚠️ Error processing your request."

# Optional: Local Test
if __name__ == "__main__":
    agent, _ = initialize_services(env="dev")
    test_message = "How do I install LlamaIndex?"
    result = process_message(agent, test_message)
    print(result)
