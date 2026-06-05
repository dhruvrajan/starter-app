import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI

_pool: asyncpg.Pool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pool
    _pool = await asyncpg.create_pool(dsn=os.environ["DATABASE_URL"])
    yield
    if _pool:
        await _pool.close()


app = FastAPI(lifespan=lifespan)


async def get_pool() -> asyncpg.Pool:
    assert _pool is not None, "DB pool not initialized"
    return _pool


@app.get("/health")
async def health():
    return {"status": "ok"}
