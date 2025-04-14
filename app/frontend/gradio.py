"""
frontend/gradio.py

Provides the Gradio-based frontend chat interface.
Connects to FastAPI backend for chat functionality and streams responses.
"""

import gradio as gr
import requests
from app.utils.logger.logger import setup_logger

# Initialize logger
logger = setup_logger()


def stream_response(message: str, history: list):
    """
    Stream response from FastAPI backend endpoint for Gradio UI.

    Args:
        message (str): User input message.
        history (list): Chat history (unused but required by Gradio interface).

    Yields:
        str: Streamed response, character by character.
    """
    if not message:
        yield "⚠️ Please provide a message."
        return

    try:
        response = requests.post("http://localhost:8000/message/", json={"message": message})
        response.raise_for_status()  # Raise error for bad responses
        reply_message = response.json().get("message", "")

        logger.info(f"Gradio received response: {reply_message}")

        # Stream response character by character
        partial_response = ""
        for char in reply_message:
            partial_response += char
            yield partial_response

    except requests.RequestException as e:
        logger.error(f"Error communicating with FastAPI backend: {e}")
        yield f"🚨 Error: {str(e)}"


def mount_gradio_app(app):
    """
    Mounts Gradio interface to FastAPI app.

    Args:
        app (FastAPI): FastAPI application instance.
    """
    chat_interface = gr.ChatInterface(
        fn=stream_response,
        title="🦙 Chat with LlamaIndex Docs Agent!",
        examples=[
            "How do I install LlamaIndex?",
            "What is a workflow and how can I implement it?",
            "How can I build advanced retrieval with LlamaIndex?"
        ],
        description=(
            "This assistant helps you navigate LlamaIndex documentation and explore solutions."
            " It will try internal documentation first, and if not sufficient, search the web."
        ),
        theme="soft",  # Optional: clean light theme
        type="messages"  # ✅ Fixes deprecation warning
    )

    gr.mount_gradio_app(app, chat_interface, path="/gradio")
    logger.info("✅ Gradio interface mounted at /gradio")
