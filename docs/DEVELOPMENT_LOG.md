# Development Log

## Phase 1 — Foundation

### Implemented

- Scaffolded the React frontend with Vite.
- Added an Axios health-check client, visible connection state, and Vite development proxy.
- Added a FastAPI application and `GET /api/v1/health`.
- Added environment-based backend settings, SQLAlchemy engine setup, and PostgreSQL/PostGIS Docker Compose configuration.
- Added focused frontend and backend health tests and initial setup/data integrity documentation.

### Validation

- Runtime versions observed: Node.js 24.21.0 and Python 3.13.14.
- Backend tests: 1 passed. Starlette emitted a deprecation warning for AnyIO's `BlockingPortal` alias.
- Frontend tests: 4 passed; lint and production build passed.
- Started FastAPI on `127.0.0.1:8001` and Vite on `127.0.0.1:5173`. Both direct URLs returned HTTP 200. The Vite `/api/v1/health` proxy also returned HTTP 200 with the same response as FastAPI: `{"status":"ok","service":"orca-india-api"}`.
- Inspected `/openapi.json`: the health response schema is an object with string-valued properties (`dict[str, str]`).
- The React backend status component displays Loading during the request, Connected only when both expected health fields match, and Disconnected on network errors or an unexpected payload.
- Opened the live Vite page in a browser; the rendered status was Connected.
- The initial broad version ranges resolved to FastAPI 0.162.5 and Pydantic 2.14.3. FastAPI required Pydantic >=2.9.0; that Pydantic release required the exact `pydantic-core==2.50.4`. Pip's subsequent fetches for package metadata and wheels timed out or failed DNS resolution, including for `pydantic-core`, then backtracked and printed `ResolutionImpossible`. This was a package-index/network retrieval failure, not evidence that the direct requirement ranges were mutually incompatible.
- Replaced the open-ended runtime ranges with verified pins: FastAPI 0.115.12, Uvicorn 0.34.0, pydantic-settings 2.8.1, SQLAlchemy 2.0.40, and Psycopg 3.2.6. These releases declare Python 3.13 support where classifiers are published; SQLAlchemy's and Psycopg's CPython 3.13 Windows wheels were selected by pip.
- Moved test-only dependencies to `requirements-dev.txt` (pytest 8.3.5 and HTTPX 0.28.1). FastAPI 0.115.12 resolved Starlette 0.46.2 (`>=0.40.0,<0.47.0`) and Pydantic 2.14.3 (`>=1.7.4,<3.0.0`); the complete set passed `pip install --dry-run --ignore-installed --only-binary=:all:` under Python 3.13.14.
- Corrected dependencies installed successfully. `pip check`: no broken requirements. Backend tests: 1 passed. A live PostGIS/database check was not run.

### Next

- Continue Phase 2 with dashboard components and map. Do not display marine observations until verified data sources are integrated.

## Database and Geospatial Foundation — 2026-11-13

### Implemented

- Made SQLAlchemy engine creation lazy and environment-only. `DATABASE_URL` is optional at API startup, is normalized to Psycopg 3, and never falls back to an embedded password. Added request-scoped sessions, pool pre-ping, and safe HTTP 503 handling for missing configuration or connection failures.
- Added SQLAlchemy models for `CoastalRegion`, `CoastalState`, `CoastalLocation`, `DataProvider`, `OceanObservation`, and `DataIngestionLog`. Spatial region/state boundaries and optional location points use SRID 4326 geometry with GiST indexes. Observation raster data is represented only by an optional external file URI; no sample records were seeded.
- Added `GET /api/v1/health/db`, `GET /api/v1/regions`, and paginated/filterable `GET /api/v1/locations`.
- Added Alembic configuration and initial migration `20261113_01`. It creates PostGIS only when available, builds the six tables and spatial indexes, and deliberately refuses a destructive initial downgrade.
- Updated `.env.example`, Docker Compose's PostGIS host port (5433 by default), README, and database/pgAdmin setup documentation.

### Database environment findings

- The PostgreSQL 18 Windows service is running and accepting TCP connections on port 5432. The installed PostgreSQL server binary and client report 18.4.
- SQL authentication to the running server could not be completed: PostgreSQL requested a password, and no root `.env`, `DATABASE_URL` environment variable, `PGPASSWORD`, or user `pgpass.conf` was configured. Therefore the server's SQL `SHOW server_version`, database list, and installed-extension catalog could not be queried.
- PostGIS is unavailable for this local PostgreSQL installation: no `postgis*.control` files were found in `C:\Program Files\PostgreSQL\18\share\extension`, and no PostGIS shared libraries were found in `C:\Program Files\PostgreSQL\18\lib`.
- Docker was not available in PATH. No database was created or modified, no extension was enabled, and no migration was applied to the live server.

### Validation

- Pinned dependency dry run passed for Python 3.13.14; Alembic 1.15.2, GeoAlchemy2 0.18.1, Mako 1.3.9, and MarkupSafe 3.0.2 installed successfully. `pip check`: no broken requirements.
- Backend tests: **8 passed, 1 skipped**. The skipped test requires a PostGIS-enabled database URL; the remaining tests cover model metadata/DDL, isolated SQLite CRUD, safe no-database API behavior, response schemas, and offline migration SQL.
- Alembic reports `20261113_01 (head)`. `alembic upgrade head --sql` generated PostgreSQL SQL with `CREATE EXTENSION`, all six tables, and GiST indexes; it does not apply the migration.
- Frontend tests: **4 passed**; lint and production build passed.
- Live API `GET /api/v1/health`: HTTP 200. Live frontend root and proxied health endpoint: HTTP 200. Database health, regions, and locations return explicit HTTP 503 `database_not_configured` responses until `DATABASE_URL` is set.

### Manual steps still required

1. Install a PostGIS build that supports PostgreSQL 18 on Windows x64; the installer must provide the `share\extension` control files and PostGIS shared library for this PostgreSQL instance.
2. In pgAdmin, inspect existing databases before creating `orca_india`; configure an authorized database role and set its URL in the root `.env`.
3. In the target database, run `CREATE EXTENSION IF NOT EXISTS postgis;` and `SELECT PostGIS_Full_Version();`.
4. From `backend`, run `.\.venv\Scripts\python.exe -m alembic upgrade head`; verify tables and GiST indexes in pgAdmin.
5. To run the spatial test, set `ORCA_TEST_DATABASE_URL` to a dedicated PostGIS-enabled test database and rerun `python -m pytest backend/tests`.
