from typing import Dict, Any
from fastapi import APIRouter
import psutil

from app.core.config import settings
from app.database.session import check_db_connection
from app.schemas.health import HealthResponse
from app.food_scanner.ocr_engine import get_ocr_engine
from app.food_scanner.service import RECENT_SCAN_METRICS

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


@router.get("/health/metrics", tags=["Health", "Monitoring"])
def get_system_metrics() -> Dict[str, Any]:
    """
    Returns real-time memory usage (RSS/VMS), system memory limits,
    OCR engine initialization state, and recent scan pipeline processing times.
    """
    proc = psutil.Process()
    mem = proc.memory_info()
    sys_mem = psutil.virtual_memory()
    engine = get_ocr_engine()

    # Calculate average timing from recent scans
    recent_list = list(RECENT_SCAN_METRICS)
    if recent_list:
        avg_total = round(sum(m["total_ms"] for m in recent_list) / len(recent_list), 2)
        avg_ocr = round(sum(m["ocr_ms"] for m in recent_list) / len(recent_list), 2)
        avg_prep = round(sum(m["preprocess_ms"] for m in recent_list) / len(recent_list), 2)
    else:
        avg_total = avg_ocr = avg_prep = 0.0

    return {
        "status": "healthy",
        "process_memory": {
            "rss_mb": round(mem.rss / (1024 * 1024), 2),
            "vms_mb": round(mem.vms / (1024 * 1024), 2),
            "percent": round(proc.memory_percent(), 2),
        },
        "system_memory": {
            "total_mb": round(sys_mem.total / (1024 * 1024), 2),
            "available_mb": round(sys_mem.available / (1024 * 1024), 2),
            "used_percent": sys_mem.percent,
        },
        "ocr_engine": {
            "engine": engine.__class__.__name__,
            "is_initialized": getattr(engine, "is_initialized", lambda: False)(),
        },
        "performance": {
            "total_scans_recorded": len(recent_list),
            "avg_total_ms": avg_total,
            "avg_ocr_ms": avg_ocr,
            "avg_preprocess_ms": avg_prep,
            "recent_scans": recent_list[-5:],
        },
    }
