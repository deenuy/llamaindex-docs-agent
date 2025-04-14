"""
clients/

This module initializes and manages external service clients.
Includes vector databases like Qdrant and external APIs like Tavily for web search.
Provides centralized setup and health checks for external dependencies.
"""

from app.clients.tavily import get_tavily_client
from app.clients.qdrant import get_qdrant_client

if __name__ == "__main__":
    tavily_client = get_tavily_client()
    print(tavily_client.search(query="LlamaIndex API example"))

    qdrant_client = get_qdrant_client()
    print(qdrant_client.get_collections())
