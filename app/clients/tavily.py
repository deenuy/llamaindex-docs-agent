"""
clients/tavily.py

This module provides a factory function to initialize the Tavily web search client.

Tavily is used for real-time web search queries to supplement vector-based retrieval,
especially for live or long-tail information not covered in our internal documentation.

Usage:
    from app.clients.tavily import get_tavily_client
    tavily_client = get_tavily_client()
    response = tavily_client.search(query="LlamaIndex examples")
"""
import os
from tavily import TavilyClient
from app.utils.config.config_loader import ConfigLoader
from app.utils.logger.logger import setup_logger
from dotenv import load_dotenv

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

def get_tavily_client() -> TavilyClient:
    """
    Initializes and returns the Tavily client.

    Returns:
        TavilyClient: Configured Tavily client instance.
    """
    try:
        # Load environment variable

        api_key = os.getenv("TAVILY_API_KEY")

        if not api_key:
            raise ValueError("❌ Tavily API key not found in config. Please check your environment or config file.")

        client = TavilyClient(api_key=api_key)

        # Optional: Dry run to confirm initialization
        logger.info("✅ Tavily client initialized successfully.")

        return client

    except Exception as e:
        logger.error(f"❌ Failed to initialize Tavily client: {e}")
        raise
