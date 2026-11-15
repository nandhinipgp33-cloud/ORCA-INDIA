from typing import Literal

from pydantic import BaseModel

class DatabaseHealthResponse(BaseModel):
    status: Literal["connected"]
    database: str
    postgis_enabled: bool
    postgis_version: str | None
