"""
retrieval_engine/query_tools.py

This module provides factory functions to build query tools for the agent.
Encapsulates vector search and summary search tools for reuse.
"""

from llama_index.core.tools import QueryEngineTool
from llama_index.core.query_engine import BaseQueryEngine
from app.utils.logger.logger import setup_logger

logger = setup_logger()


def create_summary_tool(summary_engine: BaseQueryEngine) -> QueryEngineTool:
    """
    Creates a query tool for handling summarization queries.

    Args:
        summary_engine (BaseQueryEngine): The summary engine instance.

    Returns:
        QueryEngineTool: Configured tool for summarization queries.
    """
    logger.info("Creating summary query tool...")
    return QueryEngineTool.from_defaults(
        query_engine=summary_engine,
        description="Summarization queries related to LlamaIndex documentation."
    )


def create_vector_tool(vector_engine: BaseQueryEngine) -> QueryEngineTool:
    """
    Creates a query tool for handling vector search queries.

    Args:
        vector_engine (BaseQueryEngine): The vector search engine instance.

    Returns:
        QueryEngineTool: Configured tool for vector search queries.
    """
    logger.info("Creating vector query tool...")
    return QueryEngineTool.from_defaults(
        query_engine=vector_engine,
        description="Retrieve specific context from LlamaIndex documentation."
    )


def initialize_query_tools(config: dict) -> tuple:
    """
    Initialize both vector and summary query tools.

    Args:
        config (dict): Application configuration.

    Returns:
        tuple: (vector_tool, summary_tool)
    """
    from app.retrieval_engine.vector_search_engine import initialize_vector_engine
    from app.retrieval_engine.summary_engine import initialize_summary_engine

    vector_engine = initialize_vector_engine(config)
    summary_engine = initialize_summary_engine(config)

    vector_tool = create_vector_tool(vector_engine)
    summary_tool = create_summary_tool(summary_engine)

    logger.info("✅ Query tools initialized successfully.")
    return vector_tool, summary_tool


# Optional: Test Run
if __name__ == "__main__":
    from app.utils.config.config_loader import ConfigLoader

    config_loader = ConfigLoader(env="dev")
    config = config_loader.load_config()

    vector_tool, summary_tool = initialize_query_tools(config)

    print(vector_tool)
    print(summary_tool)
