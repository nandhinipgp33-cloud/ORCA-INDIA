# Database and Geospatial Foundation

## Current workstation findings

- The Windows service `postgresql-x64-18` is running and accepting TCP connections on port 5432. The installed `psql` client reports PostgreSQL 18.4. The server patch version could not be queried because password authentication is enabled and no database credentials are configured in the workspace.
- No root `.env`, `DATABASE_URL` environment variable, or user `pgpass.conf` was present.
- PostGIS is **not installed/available for this PostgreSQL 18 instance**: `C:\Program Files\PostgreSQL\18\share\extension\postgis*.control` and `C:\Program Files\PostgreSQL\18\lib\postgis*` were absent. `docker` is also not installed/in PATH.
- No database was created or modified and no extension was enabled.

To use the existing PostgreSQL 18 server, install a PostGIS build that explicitly supports PostgreSQL 18 on Windows x64. The installation must put PostGIS extension control/SQL files under that PostgreSQL installation's `share\extension` directory and the PostGIS shared library under its `lib` directory. Then restart/reload the server if the installer requires it. PostGIS is not provided by psycopg, GeoAlchemy2, or this application's migration.

## Connection configuration

The API reads `DATABASE_URL` from the root `.env`, through Pydantic Settings. The SQLAlchemy URL uses Psycopg 3:

```text
postgresql+psycopg://<user>:<password>@<host>:<port>/<database>
```

Copy `.env.example` to `.env`, replace every placeholder with the credentials for a database you are authorized to use, and never commit `.env`. URL-encode special characters in the username/password. No database URL is embedded as a runtime fallback: the API starts without a database, while database-backed endpoints return a clear HTTP 503 until configured. SQLAlchemy creates its engine lazily and uses `pool_pre_ping`; request sessions are closed after each request.

The root `docker-compose.yml` is an alternative local PostGIS service using `postgis/postgis:16-3.4`. It maps to host port 5433 by default to avoid the detected local PostgreSQL service on 5432. When using Compose, set `DATABASE_URL` to port 5433. Docker was unavailable during this inspection, so the Compose service was not started or validated. Do not start a second database on a port already in use.

## Initial schema

Alembic creates six empty, normalized tables:

- `coastal_regions` and `coastal_states`: extensible records for mainland and island regions; no state list or geography is seeded.
- `coastal_locations`: named coastal places with validated latitude/longitude and optional WGS 84 point geometry.
- `data_providers`: provider identity, attribution, license reference and provider metadata.
- `ocean_observations`: parameter, value, unit, point coordinates, observation/retrieval times, provider, dataset identifier, resolution, quality/status metadata, and optional external `file_uri`.
- `data_ingestion_logs`: provider-scoped ingestion status and record counts.

Region/state boundaries and location points use GeoAlchemy2 PostGIS geometry types with SRID 4326 and explicit GiST indexes in the migration. Observation coordinates are stored as latitude/longitude. Raw satellite rasters are not stored in these tables; `file_uri` is only a reference. There are no fake observations, providers, regions, or locations.

## Create, migrate, and verify

For the existing PostgreSQL service:

1. Install PostGIS compatible with PostgreSQL 18, then use pgAdmin to inspect available databases before creating anything. Create `orca_india` only if it does not already exist, and use an authorized role with database ownership/extension privileges.
2. In pgAdmin, connect to the target database and run:

   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   SELECT PostGIS_Full_Version();
   ```

3. Copy `.env.example` to `.env`, set `DATABASE_URL` to the actual host, port, database, user, and password, and verify the connection:

   ```powershell
   Set-Location backend
   .\.venv\Scripts\python.exe -m alembic current
   .\.venv\Scripts\python.exe -m alembic upgrade head
   ```

The migration also contains `CREATE EXTENSION IF NOT EXISTS postgis`, so it will fail clearly if the server-side PostGIS package is missing or the database role cannot create the extension. It creates schema only; it does not insert geographic or observation data. The initial downgrade intentionally refuses to drop tables/data.

Verify after migration:

```sql
SELECT PostGIS_Full_Version();
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public' AND indexdef ILIKE '% USING gist %'
ORDER BY indexname;
```

## pgAdmin inspection

In pgAdmin, expand **Servers → your server → Databases → orca_india → Schemas → public → Tables**, then refresh the Tables node after migration. Use **Query Tool** on `orca_india` for the verification SQL above. The initial migration creates the six domain tables plus Alembic's `alembic_version` table.

## API behavior

- `GET /api/v1/health/db` tests database access and reports whether the PostGIS extension is enabled/versioned.
- `GET /api/v1/regions` returns an empty list until region records are loaded from a verified geographic dataset.
- `GET /api/v1/locations` supports optional `state_id`/`region_id` filters and bounded `limit`/`offset`; it is also empty until locations are populated.
- Missing configuration and connection failures return safe HTTP 503 errors. The service remains runnable without PostgreSQL.

## Tests

Backend tests use an isolated in-memory SQLite database for CRUD on non-spatial models and generate PostgreSQL migration SQL offline. They do not write to the local PostgreSQL server. To exercise PostGIS against a dedicated test database, set `ORCA_TEST_DATABASE_URL` and run `python -m pytest backend/tests`; that opt-in test checks `PostGIS_Full_Version()` and an `ST_Contains` spatial query. Do not point it at a database containing data you need to preserve.
