# Starter App

FastAPI + asyncpg + Procrastinate + PostgreSQL (pgvector + AGE).

## Stack

| Layer | Tool |
|---|---|
| API | FastAPI + uvicorn |
| DB driver | asyncpg |
| Background jobs | Procrastinate (psycopg3) |
| Migrations | dbmate |
| Database | PostgreSQL 17 + pgvector + AGE |
| Dev env | mise + uv |

---

## Local dev setup

### Prerequisites

Install these manually before anything else:

- **mise** — manages python, uv, dbmate, ruff, ty, pre-commit: https://mise.jdx.dev/getting-started.html
- **Docker** — needed for postgres (and optionally the full stack): https://docs.docker.com/get-docker/

### First-time setup

Run these once after cloning:

```bash
mise install          # installs python 3.12, uv, dbmate, ruff, ty, pre-commit
mise run install      # installs Python deps into backend/.venv
mise run hooks        # wires up pre-commit git hooks
```

### Running locally

Postgres runs in Docker; the app code runs natively.

```bash
mise run db           # start postgres container (keep this running)
mise run migrate      # apply pending migrations (run after db is healthy)
```

Then in separate terminals:

```bash
mise run backend      # FastAPI on http://localhost:8000 with --reload
mise run worker       # procrastinate worker
```

Other tasks:

```bash
mise run test         # pytest
mise run lint         # ruff + ty
```

`DATABASE_URL` is pre-configured in `mise.toml` — no `.env` file needed locally.

### Full stack in Docker

Runs everything in containers (no local Python needed):

```bash
docker compose up --build
```

- API: http://localhost:8000
- Frontend: http://localhost:3000

---

## How to add a table

### 1. Create a migration

Run from the repo root:

```bash
dbmate new create_items
# creates db/migrations/<timestamp>_create_items.sql
```

Edit the generated file:

```sql
-- migrate:up
CREATE TABLE items (
    id         BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name       TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- migrate:down
DROP TABLE items;
```

### 2. Apply it

```bash
mise run migrate
# or in Docker: docker compose run --rm migrate
```

### 3. Query it from FastAPI

```python
# backend/backend/main.py
from fastapi import Depends
import asyncpg
from backend.main import app, get_pool

@app.get("/items")
async def list_items(pool: asyncpg.Pool = Depends(get_pool)):
    rows = await pool.fetch("SELECT id, name, created_at FROM items ORDER BY id")
    return [dict(r) for r in rows]

@app.post("/items")
async def create_item(name: str, pool: asyncpg.Pool = Depends(get_pool)):
    row = await pool.fetchrow(
        "INSERT INTO items (name) VALUES ($1) RETURNING id, name, created_at",
        name,
    )
    return dict(row)
```

`get_pool()` returns the connection pool initialised at startup. Use `pool.fetch` for multiple rows, `pool.fetchrow` for one, `pool.fetchval` for a scalar, `pool.execute` for writes with no return.

---

## How to add a background task

```python
# backend/backend/worker.py

@app.task
async def send_email(address: str, subject: str) -> None:
    ...  # implement

# defer from anywhere (e.g. an API endpoint):
await send_email.defer_async(address="user@example.com", subject="Hi")
```

The worker picks it up automatically. Task state is stored in the `procrastinate_*` tables, applied by the worker on startup.

---

## How to use pgvector

```sql
-- in a migration:
ALTER TABLE items ADD COLUMN embedding vector(1536);
CREATE INDEX ON items USING hnsw (embedding vector_cosine_ops);
```

```python
rows = await pool.fetch(
    "SELECT id, name FROM items ORDER BY embedding <=> $1 LIMIT 5",
    "[0.1, 0.2, ...]",
)
```

---

## How to use AGE (graph)

AGE requires loading the extension and setting the search path per session:

```python
async with pool.acquire() as conn:
    await conn.execute("LOAD 'age'")
    await conn.execute("SET search_path = ag_catalog, \"$user\", public")
    await conn.execute("SELECT create_graph('my_graph')")
    await conn.execute(
        "SELECT * FROM cypher('my_graph', $$ CREATE (:Person {name: 'Alice'}) $$) AS (v agtype)"
    )
```
