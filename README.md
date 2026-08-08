# futurewell-system

FastAPI backend for FutureWell (Heart Age MY). Async SQLAlchemy + MySQL. The
frontend is a separate project (`futurewell-ui`).

## Layout

```
app/
  core/            config.py, db.py (engine, Base, session)
  api/routes/      health.py
  modules/         vertical slices, one per feature:
    awareness/     GET /api/awareness              (CAUSE_OF_DEATH lookup)
    clinics/       GET /api/clinics[/clusters]     (PUBLIC_CLINIC filter/facets/clusters)
    risk/          POST /api/risk                  (Framingham CVD, no DB)
    guidance/      POST /api/guidance              (LIFESTYLE_TIP -> Gemini + fallback)
db/
  futurewell_erd_data_import.sql   authoritative schema + seed (3 reference tables)
tests/                             pytest unit tests per module
```

## Run locally

`docker-compose.local.yml` runs only the **DB infrastructure** (MySQL + Adminer),
mirroring production where the database is a standalone managed resource. The app
runs locally and the schema/seed is loaded by the start script, not baked into
compose.

First install deps once:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip3 install -r requirements.txt
```

Then start everything (DB + schema/seed + app):

```bash
./scripts/local-start.sh   # starts MySQL, loads db/futurewell_erd_data_import.sql, runs uvicorn
./scripts/local-stop.sh    # stops containers and resets the DB (down -v)
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Health: http://localhost:8000/api/health, DB: `/api/health/db`
- Adminer (DB browser): http://localhost:8082

The start script reloads the schema + seed on every run (the import is
idempotent), so the reference tables are always in a known state. Set
`GEMINI_API_KEY` in your shell before starting to enable Gemini guidance;
without it, guidance uses the template fallback.

## Tests

```bash
python3 -m pytest tests/ -q
```

## Deploy (Coolify)

`docker-compose.yml` deploys the backend only. MySQL is a separate managed
Coolify resource; set `DATABASE_URL`, `CORS_ORIGINS`, and `GEMINI_API_KEY` in the
backend resource's environment. Import `db/futurewell_erd_data_import.sql` into
the managed DB once.
