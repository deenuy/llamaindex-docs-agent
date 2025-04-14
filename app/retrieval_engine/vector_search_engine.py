"""
retrieval_engine/vector_search_engine.py

This module sets up the vector search engine using Qdrant as the vector store backend.
It initializes the vector store client and constructs the query engine for semantic search.
"""

from typing import Any
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import VectorStoreIndex
from qdrant_client import QdrantClient

from app.utils.logger.logger import setup_logger
from app.utils.config.config_loader import ConfigLoader

# Initialize logger
logger = setup_logger()

def initialize_vector_engine(config: dict, qdrant_client: QdrantClient) -> VectorStoreIndex:
    """
    Initializes the Vector Search Engine using Qdrant vector store.

    Args:
        config (dict): Application configuration dictionary.
        qdrant_client (QdrantClient): Instance of the Qdrant client.

    Returns:
        VectorStoreIndex: Initialized vector store index for querying.
    """
    collection_name = config["paths"]["collection"]
    logger.info(f"Initializing vector engine for collection: {collection_name}")

    vector_store = QdrantVectorStore(
        client=qdrant_client,
        collection_name=collection_name,
        enable_hybrid=True
    )

    vector_index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    logger.info("✅ Vector engine initialized successfully.")

    return vector_index


# Optional: local test
if __name__ == "__main__":
    from app.clients.qdrant import get_qdrant_client
    from app.utils.config.config_loader import ConfigLoader

    config_loader = ConfigLoader(env="dev")
    config = config_loader.load_config()

    qdrant_client = get_qdrant_client()
    vector_index = initialize_vector_engine(config, qdrant_client)

    print(vector_index)
