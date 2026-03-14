# Financial Freedom API

Litestar API for the Financial Freedom budgeting app.

## Run with uv

From the repository root:

```powershell
uv sync
uv run litestar --app main:app run
```

That starts the API locally and serves the routes under:

```text
http://localhost:8000/api
```

If you want auto-reload during development:

```powershell
uv run litestar --app main:app run --reload
```

## Environment

The app loads environment variables from either:

- `.env`
- `env`

Common values:

```env
API_HOST=0.0.0.0
API_PORT=8000
LITESTAR_DEBUG=true
DATABASE_URL=postgresql://...
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000,http://localhost:8080
```

For local frontend development, the API also allows `localhost` and `127.0.0.1`
on arbitrary ports through a CORS regex, which helps Flutter web/dev servers that
choose a dynamic port.

## Seed the database

If you have a direct Postgres connection string:

```powershell
uv run python scripts/seed_database.py --mode database
```

If you are targeting hosted Supabase and want SQL you can run in the SQL Editor:

```powershell
uv run python scripts/seed_database.py --mode sql
```

That writes:

```text
scripts/seed_database.generated.sql
```

You can also print the SQL directly:

```powershell
uv run python scripts/seed_database.py --mode sql --stdout
```

`auto` mode is the default:

- if `DATABASE_URL` exists, it seeds directly
- otherwise it generates the SQL file

Note: the Supabase service-role key by itself is not enough to run arbitrary SQL
against your private `app` schema from this script. For hosted projects, the most
reliable path is generating SQL and running it in the Supabase SQL Editor or as a
migration.

## Project entrypoints

- Litestar app: `main:app`
- Source app module: `financial_freedom_api.app:app`
- Seed script: `scripts/seed_database.py`
