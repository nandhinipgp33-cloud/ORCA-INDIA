from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import CoastalRegion
from app.schemas.regions import CoastalRegionResponse

router = APIRouter(tags=["regions"])


@router.get("/regions", response_model=list[CoastalRegionResponse])
def list_regions(db: Session = Depends(get_db)) -> list[CoastalRegion]:
    statement = select(CoastalRegion).order_by(CoastalRegion.name)
    return list(db.scalars(statement).all())
