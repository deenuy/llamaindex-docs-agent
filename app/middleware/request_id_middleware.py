import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.utils.logger.logger import request_id_ctx_var  # ✅ Import context var

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = uuid.uuid4().hex[:6]

        # ✅ Set in context var for global logger context
        request_id_ctx_var.set(request_id)

        # Store it in request state for handler-level access
        request.state.request_id = request_id

        # Call next middleware/handler
        response: Response = await call_next(request)

        # ✅ Add to response header for client visibility
        response.headers["X-Request-ID"] = request_id

        return response