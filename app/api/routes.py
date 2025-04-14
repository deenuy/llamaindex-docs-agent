# app/api/routes.py

import os
from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field
from openai import OpenAI, OpenAIError

from app.services.chat_services import process_message, initialize_services
from app.clients.qdrant import get_qdrant_client
from app.clients.tavily import get_tavily_client
from app.utils.logger.logger import setup_logger
from app.middleware.error_handler_middleware import ErrorResponse  # ✅ import error model for docs

# =========================
# ✅ Initialize
# =========================
logger = setup_logger()
agent, config = initialize_services(env="dev")
router = APIRouter()

# =========================
# ✅ Pydantic Models
# =========================
class Message(BaseModel):
    """Schema for request and response messages."""
    message: str = Field(..., description="Message from the user")

class HealthStatus(BaseModel):
    status: str
    qdrant: str
    tavily: str
    openai: str

# =========================
# ✅ Health Check Endpoint
# =========================
@router.get(
    "/health",
    response_model=HealthStatus,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["Health"],
    status_code=status.HTTP_200_OK,
)
async def health_check(request: Request) -> dict:
    """
    Health check endpoint to confirm API and external dependencies are running.

    Args:
        request (Request): FastAPI request object for logging context.

    Returns:
        dict: Health status with external services.
    """
    request_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"[{request_id}] 🔍 Performing health check...")

    health_status = {"status": "✅ API is running"}

    # Qdrant health check
    try:
        qdrant_client = get_qdrant_client()
        collections = qdrant_client.get_collections()
        health_status["qdrant"] = f"✅ Up - Collections: {[c.name for c in collections.collections]}"
        logger.info(f"[{request_id}] ✅ Qdrant health check passed.")
    except Exception as e:
        logger.error(f"[{request_id}] ❌ Qdrant health check failed: {e}")
        health_status["qdrant"] = f"❌ Down - {str(e)}"

    # Tavily health check
    try:
        tavily_client = get_tavily_client()
        _ = tavily_client.search(query="health check", include_answer="basic")
        health_status["tavily"] = "✅ Up"
        logger.info(f"[{request_id}] ✅ Tavily health check passed.")
    except Exception as e:
        logger.error(f"[{request_id}] ❌ Tavily health check failed: {e}")
        health_status["tavily"] = f"❌ Down - {str(e)}"

    # OpenAI health check
    try:
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        _ = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "ping"}]
        )
        health_status["openai"] = "✅ Up"
        logger.info(f"[{request_id}] ✅ OpenAI health check passed.")
    except OpenAIError as e:
        logger.error(f"[{request_id}] ❌ OpenAI health check failed: {e}")
        health_status["openai"] = f"❌ Down - {str(e)}"

    return health_status

# =========================
# ✅ Message Handler Endpoint
# =========================
@router.post(
    "/message/",
    response_model=Message,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
        403: {"model": ErrorResponse, "description": "Forbidden - Invalid API key"},
    },
    tags=["Chat"],
    status_code=status.HTTP_200_OK,
)
async def handle_message(request: Request, message: Message) -> Message:
    """
    Handles incoming chat messages and returns the agent's response.

    Args:
        request (Request): FastAPI request object for logging context.
        message (Message): Incoming user message.

    Returns:
        Message: Response from the agent.
    """
    request_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"[{request_id}] 📥 Received message: {message.message}")

    response = process_message(agent, message.message)

    logger.info(f"[{request_id}] 📤 Sending response: {response}")
    return Message(message=response)