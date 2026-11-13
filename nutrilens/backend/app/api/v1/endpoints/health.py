from fastapi import APIRouter
from app.core.config import settings
from app.database.session import check_db_connection
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def get_health() -> HealthResponse:
    """Returns basic health check status including database connectivity."""
    db_connected = check_db_connection()
    return HealthResponse(
        status="healthy",
        app=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database="connected" if db_connected else "disconnected",
    )
