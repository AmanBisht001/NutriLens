from contextlib import asynccontextmanager
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.products import router as products_router
from app.api.v1.endpoints.ingredients import router as ingredients_router
from app.api.v1.endpoints.categories import router as categories_router
from app.api.v1.endpoints.scans import router as scans_router
from app.api.v1.endpoints.analysis import router as analysis_router
from app.api.v1.endpoints.suitability import router as suitability_router
from app.api.v1.endpoints.journal import router as journal_router
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.health import get_health
from app.schemas.health import HealthResponse
from app.database.base import Base
from app.database.session import engine
import app.models  # noqa: F401 - ensure models are registered

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Try to initialize database tables on startup if DB is accessible
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.warning(f"Database table initialization deferred (db offline or unreachable): {e}")

    # Pre-warm PaddleOCR synchronously in a thread before accepting scan requests.
    # This eliminates the 30-60 second cold-start delay that caused "Analysis is taking
    # longer than expected" errors on the very first scan after server startup.
    def _load_and_warm_ocr_engine():
        try:
            from app.food_scanner.ocr_engine import get_ocr_engine
            engine = get_ocr_engine()
            if hasattr(engine, "_ensure_initialized"):
                engine._ensure_initialized()
                logger.info(
                    f"OCR pre-warm complete: engine={engine.__class__.__name__} "
                    f"version={getattr(engine, '_paddle_version', '?')} "
                    f"ready={engine.is_initialized()}"
                )
            else:
                logger.info(f"OCR pre-warm complete (fallback engine): {engine.__class__.__name__}")
        except Exception as exc:
            logger.warning(f"OCR pre-warm failed (non-fatal, engine will lazy-init on first scan): {exc}")

    # Run in a thread so it doesn't block the event loop, but await it so it finishes
    # before the first request is accepted. This is the key fix for the cold-start timeout.
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _load_and_warm_ocr_engine)
    except Exception as exc:
        logger.warning(f"OCR pre-warm executor error (non-fatal): {exc}")

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="NutriLens – Personalized Food Intelligence & Nutrition Decision Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS middleware configuration
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Direct /api/health endpoint as requested in Day 1 specification
@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def root_health() -> HealthResponse:
    """System health check endpoint."""
    return get_health()


@app.get("/api/health/metrics", tags=["Health", "Monitoring"])
def root_health_metrics():
    """Real-time memory (RSS/VMS) and scan pipeline performance metrics."""
    from app.api.v1.endpoints.health import get_system_metrics
    return get_system_metrics()

# Direct /api endpoints as requested in specifications
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(products_router, prefix="/api/products", tags=["Products"])
app.include_router(ingredients_router, prefix="/api/ingredients", tags=["Ingredients"])
app.include_router(categories_router, prefix="/api/categories", tags=["Categories"])
app.include_router(scans_router, prefix="/api", tags=["Food Scanner"])
app.include_router(analysis_router, prefix="/api", tags=["Nutrition Analysis"])
app.include_router(suitability_router, prefix="/api", tags=["Dietary Suitability"])
app.include_router(journal_router, prefix="/api/journal", tags=["Food Journal & Analytics"])
app.include_router(admin_router, prefix="/api/admin", tags=["Administration"])

# Include versioned API router (/api/v1)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/api/health",
    }
