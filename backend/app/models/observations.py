import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class OceanObservation(Base):
    __tablename__ = "ocean_observations"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_obs_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_obs_longitude"),
        CheckConstraint(
            "data_status IN ('observed', 'estimated', 'stale', 'invalid')",
            name="ck_obs_data_status",
        ),
        Index(
            "ix_ocean_observations_provider_parameter_time",
            "data_provider_id",
            "parameter_name",
            "observed_at",
        ),
        Index("ix_ocean_observations_observed_at", "observed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    data_provider_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("data_providers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    dataset_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    parameter_name: Mapped[str] = mapped_column(String(100), nullable=False)
    measured_value: Mapped[float] = mapped_column(Numeric(24, 12), nullable=False)
    unit: Mapped[str] = mapped_column(String(40), nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    spatial_resolution_m: Mapped[float | None] = mapped_column(
        Numeric(14, 3), nullable=True
    )
    quality_info: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    data_status: Mapped[str] = mapped_column(
        String(16), default="observed", server_default="observed", nullable=False
    )
    file_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    provider: Mapped["DataProvider"] = relationship(back_populates="observations")


class DataIngestionLog(Base):
    __tablename__ = "data_ingestion_logs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'succeeded', 'partial', 'failed')",
            name="ck_ingestion_status",
        ),
        CheckConstraint("records_read >= 0", name="ck_ingestion_records_read"),
        CheckConstraint("records_inserted >= 0", name="ck_ingestion_records_inserted"),
        CheckConstraint("records_rejected >= 0", name="ck_ingestion_records_rejected"),
        Index("ix_ingestion_provider_started", "data_provider_id", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    data_provider_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("data_providers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    dataset_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    records_read: Mapped[int] = mapped_column(
        default=0, server_default="0", nullable=False
    )
    records_inserted: Mapped[int] = mapped_column(
        default=0, server_default="0", nullable=False
    )
    records_rejected: Mapped[int] = mapped_column(
        default=0, server_default="0", nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    provider: Mapped["DataProvider"] = relationship(back_populates="ingestion_logs")
