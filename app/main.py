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
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📊 MLflow URI: {settings.MLFLOW_TRACKING_URI}")
    logger.info(f"🤖 Model: {settings.MODEL_NAME} ({settings.MODEL_STAGE})")

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
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
        track_request_metrics(method=request.method, endpoint=request.url.path, status_code=response.status_code)

        REQUEST_DURATION.labels(method=request.method, endpoint=request.url.path).observe(duration)

        return response
    finally:
        ACTIVE_REQUESTS.dec()


# Include routers
app.include_router(health.router)
app.include_router(predict.router)


# Metrics endpoint for Prometheus
@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Prometheus metrics endpoint"""
    return await metrics_endpoint()


@app.get("/")
async def root():
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
