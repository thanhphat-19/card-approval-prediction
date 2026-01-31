"""FastAPI application for Credit Card Approval Prediction."""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.metrics import ACTIVE_REQUESTS, REQUEST_DURATION, metrics_endpoint, track_request_metrics
from app.routers import health, predict

# Setup
setup_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan events for startup and shutdown"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"MLflow URI: {settings.MLFLOW_TRACKING_URI}")
    logger.info(f"Model: {settings.MODEL_NAME} ({settings.MODEL_STAGE})")

    # Eagerly load model at startup (instead of lazy loading on first request)
    from app.services.model_service import get_model_service

    logger.info("⏳ Loading model...")
    model_service = get_model_service()
    logger.info(f"Model loaded: v{model_service.version} (run_id: {model_service.run_id})")
    logger.info(f"Source: {model_service.get_model_info()['source']}")

    yield

    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Credit Card Approval Prediction API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware - configure allowed origins based on environment
# In production, set CORS_ORIGINS environment variable to restrict origins
cors_origins = (
    settings.CORS_ORIGINS.split(",") if hasattr(settings, "CORS_ORIGINS") and settings.CORS_ORIGINS else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True if cors_origins != ["*"] else False,  # Don't allow credentials with wildcard
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Request tracking middleware
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Middleware to track request metrics"""
    start_time = time.time()
    ACTIVE_REQUESTS.inc()

    try:
        response = await call_next(request)
        duration = time.time() - start_time

        # Track metrics
        track_request_metrics(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        )
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)

        return response
    finally:
        ACTIVE_REQUESTS.dec()


# Include routers
app.include_router(health.router)
app.include_router(predict.router)


# Metrics endpoint for Prometheus
@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Prometheus metrics endpoint."""
    return await metrics_endpoint()


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
