"""
agents/react_agent.py

Defines the ReAct agent orchestration.
Composes tools from retrieval engines and external web search to enable intelligent responses.
"""
import os
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool, QueryEngineTool
from llama_index.core.llms import ChatMessage
from app.utils.config.config_loader import ConfigLoader
from app.utils.logger.logger import setup_logger
from app.clients.tavily import get_tavily_client
from app.retrieval_engine.query_tools import initialize_query_tools
from app.retrieval_engine.router_engine import initialize_router_tool
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


def initialize_web_search_tool() -> FunctionTool:
    """
    Initializes the web search tool using Tavily.

    Returns:
        FunctionTool: Configured web search function tool.
    """
    tavily_client = get_tavily_client()

    def tavily_search(query: str) -> str:
        response = tavily_client.search(query=query, include_answer="basic")
        return response.get("answer", "No answer found.")

    logger.info("✅ Web search tool (Tavily) initialized successfully.")
    return FunctionTool.from_defaults(fn=tavily_search)


def initialize_react_agent(router_tool: QueryEngineTool, web_search_tool: FunctionTool) -> ReActAgent:
    """
    Initializes the ReAct agent with retrieval and web search tools.

    Args:
        router_tool (QueryEngineTool): The router tool for internal knowledge queries.
        web_search_tool (FunctionTool): The web search tool for external lookups.

    Returns:
        ReActAgent: Configured ReAct agent instance.
    """
    system_prompt = (
        "You are a helpful assistant for developers working with LlamaIndex."
        " Prioritize internal documentation retrieval. If documentation lacks clear answers,"
        " perform a web search. Provide concise and useful responses."
    )

    chat_history = [ChatMessage.from_str(system_prompt, role="system")]

    agent = ReActAgent.from_tools(
        tools=[router_tool, web_search_tool],
        chat_history=chat_history,
        verbose=True,
    )

    logger.info("✅ ReAct agent initialized successfully.")
    return agent


# Optional: Local test
if __name__ == "__main__":
    from app.utils.config.config_loader import ConfigLoader

    config_loader = ConfigLoader(env="dev")
    config = config_loader.load_config()

    # Step 1: Initialize internal tools
    vector_tool, summary_tool = initialize_query_tools(config)

    # Step 2: Compose router tool
    router_tool = initialize_router_tool(vector_tool, summary_tool)

    # Step 3: Initialize web search tool
    web_search_tool = initialize_web_search_tool()

    # Step 4: Initialize ReAct agent
    agent = initialize_react_agent(router_tool, web_search_tool)
    print(agent)
