import asyncio
import os

import procrastinate

app = procrastinate.App(
    connector=procrastinate.PsycopgConnector(conninfo=os.environ["DATABASE_URL"]),
)


async def _process_message(message: str) -> None:
    print(f"Processing: {message}")


@app.task
async def example_task(message: str) -> None:
    await _process_message(message)


async def main() -> None:
    async with app.open_async():
        await app.schema_manager.apply_schema_async()
        await app.run_worker_async()


if __name__ == "__main__":
    asyncio.run(main())
