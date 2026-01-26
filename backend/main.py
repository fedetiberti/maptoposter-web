"""
MapToPoster Web API - FastAPI Application
"""
# Fix SSL certificates on macOS - must be done BEFORE importing requests/urllib3
import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.routes import router
from core.config import settings
from core.jobs import cleanup_expired_jobs

import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: create output directories
    os.makedirs(settings.cache_dir, exist_ok=True)
    os.makedirs(settings.output_dir, exist_ok=True)

    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())

    yield

    # Shutdown: cancel cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


async def periodic_cleanup():
    """Periodically clean up expired jobs and files."""
    while True:
        await asyncio.sleep(15 * 60)  # Every 15 minutes
        cleanup_expired_jobs()


# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="MapToPoster API",
    description="Generate beautiful map posters on demand",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "maptoposter-api"}


@app.get("/health")
async def health():
    """Health check for monitoring."""
    return {"status": "ok"}
