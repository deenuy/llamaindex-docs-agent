# app/middleware/error_handler_middleware.py

from fastapi.responses import JSONResponse
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.utils.logger.logger import setup_logger
from pydantic import BaseModel
import traceback

logger = setup_logger()

# ✅ Reusable Error Response Schema
class ErrorResponse(BaseModel):
    error: str
    request_id: str
    details: str = None  # Optional: stack trace or error details

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = getattr(request.state, "request_id", "unknown")

        try:
            response = await call_next(request)

        except StarletteHTTPException as http_exc:
            logger.error(
                f"[{request_id}] 🚨 HTTP error: {http_exc.detail} "
                f"(Status: {http_exc.status_code})"
            )
            response = JSONResponse(
                status_code=http_exc.status_code,
                content=ErrorResponse(
                    error=http_exc.detail,
                    request_id=request_id
                ).dict()
            )

        except Exception as exc:
            error_trace = "".join(traceback.format_tb(exc.__traceback__))
            logger.error(
                f"[{request_id}] 🔥 Unhandled exception: {str(exc)}\n{error_trace}"
            )
            response = JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    error="Internal server error",
                    details=str(exc),
                    request_id=request_id
                ).dict()
            )

        # ✅ Always add standard headers
        response.headers["Content-Type"] = "application/json"
        response.headers["X-Request-ID"] = request_id
        return response
