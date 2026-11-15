# System Architecture

## Foundation (Phase 1)

The React/Vite single-page application calls the FastAPI service through Axios. During local development Vite proxies `/api` to `http://127.0.0.1:8001`; the same API prefix is used in deployed environments through `VITE_API_BASE_URL`.

FastAPI assembles routers from `app/main.py`. Endpoint logic belongs in `app/api/routes/`, configuration in `app/core/`, SQLAlchemy models in `app/models/`, and database setup in `app/database/`. Database configuration is read from `DATABASE_URL`; the SQLAlchemy engine is created lazily so the API and non-database health endpoint work when the database is not configured. Database endpoints return HTTP 503 rather than hiding connection failures.

```text
Browser → React/Vite → Vite /api proxy → FastAPI → SQLAlchemy/Psycopg → PostgreSQL → PostGIS
```

Alembic migrations create the coastal region/state/location, provider, observation metadata, and ingestion-log tables. Boundary geometry uses WGS 84/SRID 4326 and GiST indexes. Region and location APIs are backed by the database and return no invented records; there are no seeded observations or boundaries. PostGIS must be installed for the target PostgreSQL server before the initial migration can be applied.

## Planned evolution

Data providers will be independent integration modules that normalize and validate provider responses before services expose provenance-bearing API schemas. The AI assistant will use backend tools and validated service outputs; it will not generate scientific measurements.
