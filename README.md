# ORCA INDIA

**Ocean Resource & Coastal Analytics** is a planned marine ecosystem intelligence platform for India's mainland coastline and island territories. It is designed to complement official services by integrating verified marine information, making it easier to explore and understand—not to replace official advisories or warnings.

The current milestone establishes the backend, a nationwide coastal/geospatial schema, and API-to-database integration. The frontend displays API connectivity; it does **not** yet display live ocean measurements. No regions, locations, providers, or observations are seeded. Observation layers will be added only after verified providers and datasets are integrated.

## Current status

- React + Vite frontend with an API connection indicator.
- FastAPI backend with a versioned health endpoint.
- SQLAlchemy models and an Alembic migration for coastal regions, states, locations, providers, observations, and ingestion logs.
- PostGIS geometry columns and GiST indexes in the initial migration.
- Database health, region-list, and location-list APIs.
- Initial backend and frontend tests.

The local PostgreSQL 18 service is listening, but its credentials are not configured in this workspace. PostGIS is not installed for that instance, so the migration has not been applied and spatial queries have not been run against the local server.

## Technology

- Frontend: React, Vite, Axios, Vitest, React Testing Library.
- Backend: Python, FastAPI, Pydantic Settings, SQLAlchemy, Alembic, GeoAlchemy2, Psycopg 3.
- Database: PostgreSQL with PostGIS. The optional Compose service uses PostgreSQL 16/PostGIS 3.4; the inspected local service is PostgreSQL 18.

Leaflet, charts, scientific data processing, and AI dependencies will be added when those modules are implemented.

## Project structure

```text
backend/
  app/
    api/routes/       # Versioned HTTP endpoints
    core/             # Environment-based configuration
    database/         # Lazy SQLAlchemy engine and request sessions
    models/           # Coastal, provider, observation, and ingestion models
    schemas/          # API response schemas
    main.py           # FastAPI app assembly
  migrations/         # Alembic environment and versioned migrations
  tests/
frontend/
  src/
    services/         # Backend API client
    test/             # Frontend test setup
docker-compose.yml    # Local PostGIS database
docs/                 # Design and data-source documentation
```

## Prerequisites

- Python 3.13.14 (validated for this foundation)
- Node.js 24.21.0 (validated for this foundation)
- npm
- PostgreSQL with a matching PostGIS installation for applying the geospatial migration
- Docker Desktop with Docker Compose (optional alternative; not available in the inspected environment)

## Run locally

### 1. Configure environment

From the project root, copy `.env.example` to `.env` and replace all placeholder connection values with credentials for a database you are authorized to use. `.env.example` is not a real credential. Copy `frontend/.env.example` to `frontend/.env.local`.

PowerShell:

```powershell
Copy-Item .env.example .env
Copy-Item frontend/.env.example frontend/.env.local
```

### 2. Configure PostgreSQL and PostGIS

The inspected local PostgreSQL service accepts connections on port 5432, but no credentials were available and PostGIS files are absent. Install a PostGIS build compatible with PostgreSQL 18 on Windows x64, then in pgAdmin inspect databases before creating `orca_india`. In that database's Query Tool, enable and verify PostGIS:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
SELECT PostGIS_Full_Version();
```

Set `DATABASE_URL` in `.env` to the authorized connection, using the `postgresql+psycopg://` driver. If you choose the alternative Compose service, it maps to port 5433 by default to avoid the local service; set the URL port to `5433`.

Optional Docker Compose alternative (requires Docker Desktop):

```powershell
docker compose up -d database
docker compose ps
```

The Compose database uses a persistent volume and includes PostGIS. Do not start it on a conflicting host port or remove its volume if you need to preserve data.

### 3. Start the API

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/Activate.ps1
python -m pip install -r backend/requirements.txt
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001 --reload
```

The API starts even when the database is not configured. In that case `/api/v1/health/db`, `/api/v1/regions`, and `/api/v1/locations` return HTTP 503 with a safe configuration/availability message.

### 4. Apply migrations

After PostGIS is installed, the target database exists, and `DATABASE_URL` is set:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic upgrade head
```

The initial migration creates the extension if available, six empty domain tables, and spatial indexes. It does not seed observations or geographic records. Its downgrade is intentionally disabled to avoid deleting data.

### 5. Start the frontend

In another terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open the URL Vite prints (normally `http://localhost:5173`). The Vite development proxy forwards `/api` requests to the local FastAPI server.

## Tests and checks

Backend, from the project root:

```powershell
python -m pip install -r backend/requirements-dev.txt
python -m pytest backend/tests
```

Without `ORCA_TEST_DATABASE_URL`, the PostGIS query test is skipped. To run it, set that variable to a dedicated PostGIS-enabled test database URL; do not use a database containing data you need to preserve. Backend CRUD tests use a temporary in-memory SQLite database and do not write to PostgreSQL.

`backend/requirements.txt` contains the pinned runtime and PostgreSQL dependencies. `backend/requirements-dev.txt` includes those dependencies plus the test runner and API test client.

Frontend:

```powershell
Set-Location frontend
npm install
npm test
npm run lint
npm run build
```

## Configuration

Root `.env` is used for backend/database configuration, including `DATABASE_URL=postgresql+psycopg://...`. The app uses Psycopg 3 and SQLAlchemy creates its engine lazily. `frontend/.env.local` is used by Vite. `.env` files are ignored by Git; do not commit credentials. `.env.example` files contain local development placeholders only.

## Database and pgAdmin

See [Database design and setup](docs/DATABASE_DESIGN.md) for the PostgreSQL 18/PostGIS inspection results, installation requirement, migration steps, schema, and pgAdmin table-inspection instructions. After migration, browse **Databases → orca_india → Schemas → public → Tables** and refresh the tree.

## Data integrity and scope

No sample measurements or unverified provider endpoints are presented as live. Provider capabilities, licensing, authentication, coverage, and freshness will be documented before integrating observations. In the meantime, the UI explicitly indicates that observation data is not connected.

## Documentation

- [System architecture](docs/SYSTEM_ARCHITECTURE.md)
- [Database design and local setup](docs/DATABASE_DESIGN.md)
- [Data source research status](docs/DATA_SOURCES.md)
- [Development log](docs/DEVELOPMENT_LOG.md)

## Screenshots

Screenshots will be added after the dashboard and map milestones.
