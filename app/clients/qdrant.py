"""
clients/qdrant.py

This module provides a factory function to initialize and configure
the Qdrant client for vector search capabilities.

It loads configurations dynamically based on the environment and
ensures that the client is properly logged for observability.

Usage:
    from app.clients.qdrant import get_qdrant_client
    qdrant_client = get_qdrant_client()
"""
import os
from qdrant_client import QdrantClient
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

# Initialize logger
logger = setup_logger()

def get_qdrant_client() -> QdrantClient:
    """
    Initializes and returns the Qdrant client.

    Returns:
        QdrantClient: Configured Qdrant client instance.
    """

    try:
        qdrant_config = config["service"]
        url = f"http://localhost:{config['qdrant']['service']['http_port']}"

        # Instantiate Qdrant client
        client = QdrantClient(
            url=url,
            prefer_grpc=False
        )

        # Proactive health check
        collections = client.get_collections()
        collection_names = [collection.name for collection in collections.collections]

        logger.info(f"✅ Qdrant client initialized at {url}.")
        logger.info(f"Existing collections: {collection_names}")

        return client

    except Exception as e:
        logger.error(f"❌ Failed to initialize Qdrant client: {e}")
        raise
