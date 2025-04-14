import os
import uvicorn

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import ORJSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from contextlib import asynccontextmanager

from app.utils.logger.logger import setup_logger
from app.api.routes import router as api_router
from app.frontend.gradio import mount_gradio_app
from app.middleware.request_id_middleware import RequestIDMiddleware
from app.middleware.error_handler_middleware import ErrorHandlerMiddleware

from dotenv import load_dotenv
load_dotenv()

# =========================
# ✅ Setup Logger
# =========================
logger = setup_logger()

# Load environment and config
env = os.getenv("ENVIRONMENT", "dev")
logger.info(f"Environment set to: {env}")

# =========================
# ✅ Rate Limiter
# =========================
limiter = Limiter(key_func=get_remote_address)

# =========================
# ✅ API Key Security
# =========================
API_KEY = os.getenv("API_KEY")  # Must be set in .env

# =========================
# ✅ Lifespan Context Manager
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 FastAPI application starting up...")
    yield
    logger.info("🛑 FastAPI application shutting down...")

# =========================
# ✅ FastAPI App Initialization
# =========================
app = FastAPI(
    title="LlamaIndex Docs Agent API 🦙",
    description="Agent-powered API for querying and summarizing LlamaIndex documentation.",
    version="0.2.0",
    contact={
        "name": "Deenu Gengiti",
        "email": "deenuy@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    default_response_class=ORJSONResponse,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# =========================
# ✅ Middlewares
# =========================

# CORS Middleware (🔒 TODO: tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with allowed domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional: HTTPS redirect middleware for production
# app.add_middleware(HTTPSRedirectMiddleware)

# Rate Limiter Middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda req, exc: ORJSONResponse(
    status_code=429,
    content={"error": "Rate limit exceeded", "request_id": getattr(req.state, "request_id", None)},
))

# ✅ Add Request ID Middleware
app.add_middleware(RequestIDMiddleware)

# ✅ Add Error Handler Middleware
app.add_middleware(ErrorHandlerMiddleware)

# ✅ API Key Middleware
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if request.url.path.startswith(("/health", "/docs", "/redoc", "/openapi.json")):
        return await call_next(request)

    api_key = request.headers.get("X-API-KEY")
    if api_key != API_KEY:
        logger.warning(f"🛑 Unauthorized access attempt: {request.client.host}")
        raise HTTPException(status_code=403, detail="Invalid or missing API Key")

    return await call_next(request)

# ✅ Logging Middleware (Enhanced with Request ID)
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = getattr(request.state, "request_id", None)
    logger.info(f"➡️ [{request_id}] Request: {request.method} {request.url}")

    response = await call_next(request)

    logger.info(f"⬅️ [{request_id}] Response: {response.status_code} for {request.method} {request.url}")
    return response

# =========================
# ✅ Root Welcome Page
# =========================
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def welcome():
    return """
    <html>
        <head><title>LlamaIndex Docs Agent 🦙</title></head>
        <body>
            <h1>🚀 Welcome to the LlamaIndex Docs Agent API</h1>
            <p>Visit <a href='/docs'>Swagger UI</a> or <a href='/redoc'>Redoc</a> for API documentation.</p>
            <p>Health Check: <a href='/health'>/health</a></p>
        </body>
    </html>
    """

# =========================
# ✅ Route Registrations
# =========================
app.include_router(api_router)
mount_gradio_app(app)

logger.info("✅ Application setup complete. Ready to serve requests.")

# =========================
# ✅ Run App (Local Dev)
# =========================
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
