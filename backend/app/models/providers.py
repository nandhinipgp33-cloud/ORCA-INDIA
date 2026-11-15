import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    JSON,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class DataProvider(Base):
    __tablename__ = "data_providers"
    __table_args__ = (
        UniqueConstraint("name", name="uq_data_providers_name"),
        UniqueConstraint("code", name="uq_data_providers_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    attribution: Mapped[str | None] = mapped_column(String(500), nullable=True)
    license_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    provider_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    observations: Mapped[list["OceanObservation"]] = relationship(
        back_populates="provider"
    )
    ingestion_logs: Mapped[list["DataIngestionLog"]] = relationship(
        back_populates="provider"
    )
