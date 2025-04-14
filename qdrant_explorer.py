#!/usr/bin/env python
"""
Qdrant Explorer - A simple tool to explore Qdrant collections
"""

import os
import json
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.tree import Tree
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

console = Console()

def connect_to_qdrant(path=None, url=None):
    """Connect to Qdrant using either path or URL"""
    try:
        if path:
            client = QdrantClient(path=path)
            console.print(f"Connected to Qdrant at path:", path, style="green")
        else:
            client = QdrantClient(url=url)
            console.print(f"Connected to Qdrant at URL:", url, style="green")
        return client
    except Exception as e:
        console.print("Error connecting to Qdrant:", str(e), style="red")
        return None

def list_collections(client):
    """List all collections in Qdrant"""
    collections = client.get_collections()

    if not collections.collections:
        console.print("No collections found in Qdrant", style="yellow")
        return

    table = Table(title="Qdrant Collections")
    table.add_column("Name", style="cyan")
    table.add_column("Vectors", style="green")
    table.add_column("Points", style="blue")
    table.add_column("Status", style="magenta")

    for collection in collections.collections:
        name = collection.name
        try:
            info = client.get_collection(name)
            vectors = ", ".join(info.config.params.vectors.keys())
            points = str(info.points_count)
            status = "✅ Ready" if collection.status == "green" else "⚠️ " + collection.status
        except Exception as e:
            vectors = "Error"
            points = "Error"
            status = f"⚠️ Error: {str(e)}"

        table.add_row(name, vectors, points, status)

    console.print(table)
    return [c.name for c in collections.collections]

def explore_collection(client, collection_name):
    """Explore details of a specific collection"""
    try:
        info = client.get_collection(collection_name)

        # Collection info
        console.print(Panel(f"Collection: {collection_name}", title="Collection Info", style="cyan"))

        # Vector configuration
        vector_tree = Tree("Vector Configuration")
        for vector_name, vector_config in info.config.params.vectors.items():
            vector_node = vector_tree.add(f"{vector_name}", style="green")
            vector_node.add(f"Size: {vector_config.size}")
            vector_node.add(f"Distance: {vector_config.distance}")
        console.print(vector_tree)

        # Collection stats
        console.print("Points count:", info.points_count, style="blue")

        # Sample points
        result, _ = client.scroll(
            collection_name=collection_name,
            limit=3,
            with_vectors=False,
            with_payload=True
        )

        if result:
            console.print("Sample Points:", style="cyan")
            for i, point in enumerate(result):
                point_id = point.id
                if isinstance(point_id, list):
                    point_id = f"UUID: {str(point_id)[:8]}..."

                point_panel = Panel(
                    Syntax(json.dumps(point.payload, indent=2), "json", theme="monokai"),
                    title=f"Point {i+1} (ID: {point_id})",
                    border_style="green"
                )
                console.print(point_panel)
        else:
            console.print("No points found in collection", style="yellow")

    except Exception as e:
        console.print(f"Error exploring collection {collection_name}:", str(e), style="red")

def search_collection(client, collection_name):
    """Search in a collection using a simple test query"""
    try:
        from llama_index.embeddings.openai import OpenAIEmbedding

        console.print("Using OpenAI to generate a test query embedding...", style="yellow")
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            console.print("Error: OPENAI_API_KEY environment variable not set", style="red")
            return

        embed_model = OpenAIEmbedding(
            model="text-embedding-3-small",
            api_key=api_key
        )

        query = input("\nEnter a search query: ")
        if not query:
            console.print("Search cancelled", style="yellow")
            return

        # Generate embedding for the query
        embedding = embed_model.get_text_embedding(query)

        # Search the collection
        search_result = client.search(
            collection_name=collection_name,
            query_vector=("text", embedding),
            limit=3
        )

        console.print(f"\nSearch Results for: '{query}'\n", style="cyan")

        if search_result:
            for i, result in enumerate(search_result):
                score = result.score
                score_color = "green" if score > 0.7 else "yellow" if score > 0.5 else "red"

                result_panel = Panel(
                    Syntax(json.dumps(result.payload, indent=2), "json", theme="monokai"),
                    title=f"Result {i+1} (Score: {score:.4f})",
                    border_style=score_color
                )
                console.print(result_panel)
        else:
            console.print("No matching results found", style="yellow")

    except ImportError:
        console.print("Error: llama_index or openai package not installed", style="red")
    except Exception as e:
        console.print("Error searching collection:", str(e), style="red")

def interactive_menu(client, path=None, url=None):
    """Interactive menu for exploring Qdrant"""
    while True:
        console.print("\nQdrant Explorer", style="bold cyan")
        console.print("1. List Collections")
        console.print("2. Explore Collection")
        console.print("3. Search Collection")
        console.print("4. Quit")

        choice = input("\nEnter your choice (1-4): ")

        if choice == "1":
            list_collections(client)

        elif choice == "2":
            collection_names = list_collections(client)
            if collection_names:
                collection_num = input(f"\nEnter collection number (1-{len(collection_names)}): ")
                try:
                    idx = int(collection_num) - 1
                    if 0 <= idx < len(collection_names):
                        explore_collection(client, collection_names[idx])
                    else:
                        console.print("Invalid collection number", style="red")
                except ValueError:
                    console.print("Please enter a valid number", style="red")

        elif choice == "3":
            collection_names = list_collections(client)
            if collection_names:
                collection_num = input(f"\nEnter collection number (1-{len(collection_names)}): ")
                try:
                    idx = int(collection_num) - 1
                    if 0 <= idx < len(collection_names):
                        search_collection(client, collection_names[idx])
                    else:
                        console.print("Invalid collection number", style="red")
                except ValueError:
                    console.print("Please enter a valid number", style="red")

        elif choice == "4":
            console.print("Goodbye!", style="green")
            break

        else:
            console.print("Invalid choice. Please try again.", style="red")

def main():
    parser = argparse.ArgumentParser(description="Qdrant Explorer - A simple tool to explore Qdrant collections")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--path", help="Path to Qdrant storage directory")
    group.add_argument("--url", help="URL to Qdrant server, e.g., http://localhost:6333")

    args = parser.parse_args()

    client = connect_to_qdrant(path=args.path, url=args.url)
    if client:
        interactive_menu(client, path=args.path, url=args.url)

if __name__ == "__main__":
    main()