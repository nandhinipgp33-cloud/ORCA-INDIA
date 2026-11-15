import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import CoastalLocation, CoastalState
from app.schemas.regions import CoastalLocationResponse

router = APIRouter(tags=["locations"])


@router.get("/locations", response_model=list[CoastalLocationResponse])
def list_locations(
    state_id: uuid.UUID | None = None,
    region_id: uuid.UUID | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[CoastalLocation]:
    statement = select(CoastalLocation).join(CoastalState)
    if state_id is not None:
        statement = statement.where(CoastalLocation.state_id == state_id)
    if region_id is not None:
        statement = statement.where(CoastalState.region_id == region_id)
    statement = statement.order_by(CoastalLocation.name).limit(limit).offset(offset)
    return list(db.scalars(statement).all())
