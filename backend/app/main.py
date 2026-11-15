import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.api.routes.health import router as health_router
from app.api.routes.locations import router as locations_router
from app.api.routes.regions import router as regions_router
from app.core.config import settings
from app.database.session import (
    DatabaseConfigurationError,
    DatabaseNotConfiguredError,
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ORCA INDIA API",
    description="Ocean Resource & Coastal Analytics API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(regions_router, prefix="/api/v1")
app.include_router(locations_router, prefix="/api/v1")


@app.exception_handler(DatabaseConfigurationError)
async def database_configuration_error_handler(
    _request: Request, error: DatabaseConfigurationError
) -> JSONResponse:
    if isinstance(error, DatabaseNotConfiguredError):
        error_code = "database_not_configured"
    else:
        error_code = "database_configuration_error"
    logger.warning("Database configuration error: %s", error)
    return JSONResponse(
        status_code=503,
        content={
            "detail": {
                "code": error_code,
                "message": str(error),
            }
        },
    )


@app.exception_handler(OperationalError)
async def database_connection_error_handler(
    _request: Request, error: OperationalError
) -> JSONResponse:
    logger.error("Database connection failed: %s", type(error).__name__)
    return JSONResponse(
        status_code=503,
        content={
            "detail": {
                "code": "database_unavailable",
                "message": "PostgreSQL is unavailable or DATABASE_URL is incorrect.",
            }
        },
    )
