from fastapi import APIRouter
from sqlalchemy import text

from app.database.session import get_engine
from app.schemas.database import DatabaseHealthResponse

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok", "service": "orca-india-api"}


@router.get("/health/db", response_model=DatabaseHealthResponse)
def get_database_health() -> DatabaseHealthResponse:
    with get_engine().connect() as connection:
        database_name = connection.scalar(text("SELECT current_database()"))
        postgis_version = connection.scalar(
            text("SELECT extversion FROM pg_extension WHERE extname = 'postgis'")
        )

    return DatabaseHealthResponse(
        status="connected",
        database=database_name,
        postgis_enabled=postgis_version is not None,
        postgis_version=postgis_version,
    )
