import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict


class CoastalRegionResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    region_type: Literal["mainland", "island"]

    model_config = ConfigDict(from_attributes=True)


class CoastalLocationResponse(BaseModel):
    id: uuid.UUID
    state_id: uuid.UUID
    name: str
    location_type: str
    latitude: float
    longitude: float

    model_config = ConfigDict(from_attributes=True)
