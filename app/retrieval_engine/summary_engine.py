"""
retrieval_engine/summary_engine.py

This module sets up the summary search engine.
It loads the pre-built SummaryIndex from persistent storage for summarization queries.
"""

from llama_index.core import load_index_from_storage, StorageContext
from llama_index.core.indices.list import SummaryIndex
from app.utils.logger.logger import setup_logger

logger = setup_logger()

def initialize_summary_engine(config: dict) -> SummaryIndex:
    """
    Initializes the summary search engine by loading the persisted SummaryIndex.

    Args:
        config (dict): Application configuration dictionary.

    Returns:
        SummaryIndex: Loaded summary index for answering summarization queries.
    """
    index_db_path = config["paths"]["index_db_dir"]
    logger.info(f"Loading summary index from: {index_db_path}")

    # Initialize storage context
    storage_context = StorageContext.from_defaults(persist_dir=index_db_path)

    # Load the summary index from storage
    summary_index = load_index_from_storage(storage_context=storage_context)

    logger.info("✅ Summary engine loaded successfully.")

    return summary_index


# Optional: Local test
if __name__ == "__main__":
    from app.utils.config.config_loader import ConfigLoader

    config_loader = ConfigLoader(env="dev")
    config = config_loader.load_config()

    summary_index = initialize_summary_engine(config)
    print(summary_index)
