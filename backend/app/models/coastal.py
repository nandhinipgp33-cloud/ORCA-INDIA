import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class CoastalRegion(Base):
    __tablename__ = "coastal_regions"
    __table_args__ = (
        CheckConstraint(
            "region_type IN ('mainland', 'island')", name="ck_coastal_regions_type"
        ),
        UniqueConstraint("name", name="uq_coastal_regions_name"),
        UniqueConstraint("slug", name="uq_coastal_regions_slug"),
        Index(
            "ix_coastal_regions_boundary_gist",
            "boundary",
            postgresql_using="gist",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    region_type: Mapped[str] = mapped_column(String(24), nullable=False)
    boundary: Mapped[object | None] = mapped_column(
        Geometry("MULTIPOLYGON", srid=4326, spatial_index=False), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    states: Mapped[list["CoastalState"]] = relationship(back_populates="region")


class CoastalState(Base):
    __tablename__ = "coastal_states"
    __table_args__ = (
        UniqueConstraint("code", name="uq_coastal_states_code"),
        Index("ix_coastal_states_region_id", "region_id"),
        Index(
            "ix_coastal_states_boundary_gist",
            "boundary",
            postgresql_using="gist",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    region_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("coastal_regions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(12), nullable=False)
    boundary: Mapped[object | None] = mapped_column(
        Geometry("MULTIPOLYGON", srid=4326, spatial_index=False), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    region: Mapped[CoastalRegion] = relationship(back_populates="states")
    locations: Mapped[list["CoastalLocation"]] = relationship(
        back_populates="state"
    )


class CoastalLocation(Base):
    __tablename__ = "coastal_locations"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_locations_latitude"),
        CheckConstraint(
            "longitude BETWEEN -180 AND 180", name="ck_locations_longitude"
        ),
        Index("ix_coastal_locations_state_id", "state_id"),
        Index(
            "ix_coastal_locations_location_gist",
            "location",
            postgresql_using="gist",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    state_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("coastal_states.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    location_type: Mapped[str] = mapped_column(String(40), nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    location: Mapped[object | None] = mapped_column(
        Geometry("POINT", srid=4326, spatial_index=False), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    state: Mapped[CoastalState] = relationship(back_populates="locations")
