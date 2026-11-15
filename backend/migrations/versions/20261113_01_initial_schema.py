"""Create the nationwide coastal and observation schema.

Revision ID: 20261113_01
Revises:
"""

from alembic import op
import geoalchemy2
import sqlalchemy as sa

revision = "20261113_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "coastal_regions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("region_type", sa.String(length=24), nullable=False),
        sa.Column(
            "boundary",
            geoalchemy2.Geometry(
                geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "region_type IN ('mainland', 'island')",
            name="ck_coastal_regions_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_coastal_regions_name"),
        sa.UniqueConstraint("slug", name="uq_coastal_regions_slug"),
    )
    op.create_index(
        "ix_coastal_regions_boundary_gist",
        "coastal_regions",
        ["boundary"],
        postgresql_using="gist",
    )

    op.create_table(
        "coastal_states",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("region_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=12), nullable=False),
        sa.Column(
            "boundary",
            geoalchemy2.Geometry(
                geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["region_id"], ["coastal_regions.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_coastal_states_code"),
    )
    op.create_index("ix_coastal_states_region_id", "coastal_states", ["region_id"])
    op.create_index(
        "ix_coastal_states_boundary_gist",
        "coastal_states",
        ["boundary"],
        postgresql_using="gist",
    )

    op.create_table(
        "coastal_locations",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("state_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("location_type", sa.String(length=40), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column(
            "location",
            geoalchemy2.Geometry(
                geometry_type="POINT", srid=4326, spatial_index=False
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_locations_latitude"),
        sa.CheckConstraint(
            "longitude BETWEEN -180 AND 180", name="ck_locations_longitude"
        ),
        sa.ForeignKeyConstraint(
            ["state_id"], ["coastal_states.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_coastal_locations_state_id", "coastal_locations", ["state_id"]
    )
    op.create_index(
        "ix_coastal_locations_location_gist",
        "coastal_locations",
        ["location"],
        postgresql_using="gist",
    )

    op.create_table(
        "data_providers",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=True),
        sa.Column("attribution", sa.String(length=500), nullable=True),
        sa.Column("license_url", sa.String(length=500), nullable=True),
        sa.Column("provider_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "enabled",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_data_providers_code"),
        sa.UniqueConstraint("name", name="uq_data_providers_name"),
    )

    op.create_table(
        "data_ingestion_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("data_provider_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("dataset_identifier", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_read", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_inserted", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_rejected", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.CheckConstraint(
            "status IN ('running', 'succeeded', 'partial', 'failed')",
            name="ck_ingestion_status",
        ),
        sa.CheckConstraint("records_read >= 0", name="ck_ingestion_records_read"),
        sa.CheckConstraint(
            "records_inserted >= 0", name="ck_ingestion_records_inserted"
        ),
        sa.CheckConstraint(
            "records_rejected >= 0", name="ck_ingestion_records_rejected"
        ),
        sa.ForeignKeyConstraint(
            ["data_provider_id"], ["data_providers.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ingestion_provider_started",
        "data_ingestion_logs",
        ["data_provider_id", "started_at"],
    )

    op.create_table(
        "ocean_observations",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("data_provider_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("dataset_identifier", sa.String(length=255), nullable=False),
        sa.Column("parameter_name", sa.String(length=100), nullable=False),
        sa.Column(
            "measured_value", sa.Numeric(precision=24, scale=12), nullable=False
        ),
        sa.Column("unit", sa.String(length=40), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "retrieved_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "spatial_resolution_m", sa.Numeric(precision=14, scale=3), nullable=True
        ),
        sa.Column("quality_info", sa.JSON(), nullable=True),
        sa.Column(
            "data_status",
            sa.String(length=16),
            server_default="observed",
            nullable=False,
        ),
        sa.Column("file_uri", sa.String(length=1024), nullable=True),
        sa.CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_obs_latitude"),
        sa.CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_obs_longitude"),
        sa.CheckConstraint(
            "data_status IN ('observed', 'estimated', 'stale', 'invalid')",
            name="ck_obs_data_status",
        ),
        sa.ForeignKeyConstraint(
            ["data_provider_id"], ["data_providers.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ocean_observations_provider_parameter_time",
        "ocean_observations",
        ["data_provider_id", "parameter_name", "observed_at"],
    )
    op.create_index(
        "ix_ocean_observations_observed_at",
        "ocean_observations",
        ["observed_at"],
    )


def downgrade() -> None:
    raise RuntimeError(
        "Initial schema downgrade is disabled to avoid deleting application data."
    )
