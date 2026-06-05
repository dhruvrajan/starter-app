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

## Quick start

## Local Dev:

First install the following:
- mise from https://mise.jdx.dev/
- 

### Full stack (Docker)

```bash
mise install
docker compose up --build
```

- API: http://localhost:8000
- Frontend: http://localhost:3000

### Local dev (no Docker for app code)

```bash
mise install          # installs python, uv, dbmate
mise run install      # uv sync --group dev
mise run db           # starts postgres in Docker
mise run migrate      # applies pending migrations
mise run backend      # FastAPI on :8000 with --reload
mise run worker       # procrastinate worker
mise run test         # pytest
```

`DATABASE_URL` is set in `mise.toml` for local dev.

---

## How to add a table

### 1. Create a migration

```bash
dbmate new create_items
# creates db/migrations/<timestamp>_create_items.sql
```

Edit the generated file:

```sql
-- migrate:up
CREATE TABLE items (
    id   BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name TEXT NOT NULL,
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
# backend/main.py
from fastapi import Depends
import asyncpg
from backend.main import get_pool

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
# backend/worker.py

@app.task
async def send_email(address: str, subject: str) -> None:
    ...  # implement

# defer from anywhere (e.g. an API endpoint):
await send_email.defer_async(address="user@example.com", subject="Hi")
```

The worker picks it up automatically. Task state is stored in the `procrastinate_*` tables (applied by `worker.py` on startup via `apply_schema_async`).

---

## How to use pgvector

```sql
-- in a migration:
ALTER TABLE items ADD COLUMN embedding vector(1536);
CREATE INDEX ON items USING hnsw (embedding vector_cosine_ops);
```

```python
# query nearest neighbours:
rows = await pool.fetch(
    "SELECT id, name FROM items ORDER BY embedding <=> $1 LIMIT 5",
    "[0.1, 0.2, ...]",  # pass as a string or use pgvector's Python type
)
```

## How to use AGE (graph)

```python
# Each session must load the AGE extension before using Cypher:
async with pool.acquire() as conn:
    await conn.execute("LOAD 'age'")
    await conn.execute("SET search_path = ag_catalog, \"$user\", public")
    await conn.execute("SELECT create_graph('my_graph')")
    await conn.execute(
        "SELECT * FROM cypher('my_graph', $$ CREATE (:Person {name: 'Alice'}) $$) AS (v agtype)"
    )
```
