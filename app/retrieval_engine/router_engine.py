"""
retrieval_engine/router_engine.py

This module sets up the router query engine.
It combines the vector search and summary search tools into a unified router engine.
"""

from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import PydanticSingleSelector
from llama_index.core.tools import QueryEngineTool
from app.utils.logger.logger import setup_logger
from app.retrieval_engine.query_tools import create_summary_tool, create_vector_tool

logger = setup_logger()

def initialize_router_tool(summary_engine, vector_engine) -> QueryEngineTool:
    """
    Initializes the router tool that intelligently routes queries
    between the summary engine and vector search engine.

    Args:
        summary_engine: The summary engine instance.
        vector_engine: The vector search engine instance.

    Returns:
        QueryEngineTool: Configured router tool.
    """
    logger.info("Initializing router tool...")

    # Build individual tools
    summary_tool = create_summary_tool(summary_engine)
    vector_tool = create_vector_tool(vector_engine)

    # Initialize the router query engine
    router_engine = RouterQueryEngine(
        selector=PydanticSingleSelector.from_defaults(),
        query_engine_tools=[summary_tool, vector_tool],
    )

    logger.info("✅ Router tool initialized successfully.")

    # Wrap router engine in a tool for agent usage
    router_tool = QueryEngineTool.from_defaults(
        query_engine=router_engine,
        description="Router engine that selects between summarization and vector search tools."
    )

    return router_tool


# Optional: Local test
if __name__ == "__main__":
    from app.utils.config.config_loader import ConfigLoader
    from app.retrieval_engine.vector_search_engine import initialize_vector_engine
    from app.retrieval_engine.summary_engine import initialize_summary_engine

    config_loader = ConfigLoader(env="dev")
    config = config_loader.load_config()

    vector_engine = initialize_vector_engine(config)
    summary_engine = initialize_summary_engine(config)

    router_tool = initialize_router_tool(summary_engine, vector_engine)
    print(router_tool)
