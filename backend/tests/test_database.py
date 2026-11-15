import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import Base, get_db, get_engine
from app.main import app
from app.models import (
    CoastalLocation,
    CoastalRegion,
    CoastalState,
    DataIngestionLog,
    DataProvider,
    OceanObservation,
)

client = TestClient(app)
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_model_metadata_contains_all_initial_entities() -> None:
    assert set(Base.metadata.tables) == {
        "coastal_regions",
        "coastal_states",
        "coastal_locations",
        "data_providers",
        "ocean_observations",
        "data_ingestion_logs",
    }


def test_spatial_models_compile_to_wgs84_postgis_columns() -> None:
    region_ddl = str(
        CreateTable(CoastalRegion.__table__).compile(dialect=postgresql.dialect())
    )
    state_ddl = str(
        CreateTable(CoastalState.__table__).compile(dialect=postgresql.dialect())
    )
    location_ddl = str(
        CreateTable(CoastalLocation.__table__).compile(dialect=postgresql.dialect())
    )

    assert "geometry(MULTIPOLYGON,4326)" in region_ddl
    assert "geometry(MULTIPOLYGON,4326)" in state_ddl
    assert "geometry(POINT,4326)" in location_ddl


def test_nonspatial_models_support_sqlite_crud() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    tables = [
        DataProvider.__table__,
        OceanObservation.__table__,
        DataIngestionLog.__table__,
    ]
    Base.metadata.create_all(engine, tables=tables)

    try:
        with Session(engine) as session:
            provider = DataProvider(
                name="Unit test provider",
                code="unit-test",
                enabled=True,
                provider_metadata={"purpose": "isolated test"},
            )
            session.add(provider)
            session.flush()

            observation = OceanObservation(
                data_provider_id=provider.id,
                dataset_identifier="unit-test-dataset",
                parameter_name="test_parameter",
                measured_value=Decimal("1.25"),
                unit="test_unit",
                latitude=Decimal("1"),
                longitude=Decimal("2"),
                observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                quality_info={"fixture": True},
            )
            ingestion = DataIngestionLog(
                data_provider_id=provider.id,
                dataset_identifier="unit-test-dataset",
                status="succeeded",
                records_read=1,
                records_inserted=1,
            )
            session.add_all([observation, ingestion])
            session.commit()

            saved_observation = session.scalar(
                select(OceanObservation).where(
                    OceanObservation.dataset_identifier == "unit-test-dataset"
                )
            )
            saved_ingestion = session.scalar(select(DataIngestionLog))

            assert saved_observation is not None
            assert saved_observation.provider.code == "unit-test"
            assert saved_observation.measured_value == Decimal("1.250000000000")
            assert saved_ingestion is not None
            assert saved_ingestion.records_inserted == 1

            saved_observation.data_status = "estimated"
            session.commit()
            updated_observation = session.get(OceanObservation, saved_observation.id)
            assert updated_observation is not None
            assert updated_observation.data_status == "estimated"

            ingestion_id = saved_ingestion.id
            session.delete(saved_ingestion)
            session.commit()
            assert session.get(DataIngestionLog, ingestion_id) is None
    finally:
        Base.metadata.drop_all(engine, tables=tables)
        engine.dispose()


def test_database_and_list_routes_report_missing_database_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    get_engine.cache_clear()

    try:
        for path in (
            "/api/v1/health/db",
            "/api/v1/regions",
            "/api/v1/locations",
        ):
            response = client.get(path)
            assert response.status_code == 503
            assert response.json()["detail"]["code"] == "database_not_configured"
    finally:
        get_engine.cache_clear()


def test_unsupported_database_driver_reports_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "database_url", "sqlite+pysqlite:///:memory:")
    get_engine.cache_clear()
    try:
        response = client.get("/api/v1/health/db")
    finally:
        get_engine.cache_clear()

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "database_configuration_error"


def test_region_and_location_routes_return_validated_schemas() -> None:
    region_id = uuid.uuid4()
    state_id = uuid.uuid4()
    region = CoastalRegion(
        id=region_id,
        name="Unit Test Region",
        slug="unit-test-region",
        region_type="mainland",
    )
    location = CoastalLocation(
        id=uuid.uuid4(),
        state_id=state_id,
        name="Unit Test Location",
        location_type="port",
        latitude=Decimal("12.5"),
        longitude=Decimal("45.5"),
    )

    class FakeSession:
        def scalars(self, statement):
            entity = statement.column_descriptions[0]["entity"]
            rows = [region] if entity is CoastalRegion else [location]
            return SimpleNamespace(all=lambda: rows)

    app.dependency_overrides[get_db] = lambda: FakeSession()
    try:
        regions_response = client.get("/api/v1/regions")
        locations_response = client.get(
            "/api/v1/locations", params={"region_id": str(region_id)}
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert regions_response.status_code == 200
    assert regions_response.json()[0]["slug"] == "unit-test-region"
    assert locations_response.status_code == 200
    assert locations_response.json()[0]["latitude"] == 12.5


def test_initial_migration_generates_nondestructive_postgresql_sql() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "alembic.ini",
            "upgrade",
            "head",
            "--sql",
        ],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    sql = result.stdout
    assert "CREATE EXTENSION IF NOT EXISTS postgis" in sql
    assert "CREATE TABLE coastal_regions" in sql
    assert "CREATE TABLE ocean_observations" in sql
    assert "USING gist" in sql
    assert "DROP TABLE" not in sql


@pytest.mark.skipif(
    not os.environ.get("ORCA_TEST_DATABASE_URL"),
    reason="Set ORCA_TEST_DATABASE_URL to a PostGIS-enabled test database.",
)
def test_postgis_spatial_query() -> None:
    from sqlalchemy.engine import make_url

    url = make_url(os.environ["ORCA_TEST_DATABASE_URL"])
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg")
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            version = connection.scalar(text("SELECT PostGIS_Full_Version()"))
            contains_point = connection.scalar(
                text(
                    "SELECT ST_Contains("
                    "ST_GeomFromText('POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))', 4326), "
                    "ST_SetSRID(ST_Point(5, 5), 4326))"
                )
            )
        assert version
        assert contains_point is True
    finally:
        engine.dispose()
