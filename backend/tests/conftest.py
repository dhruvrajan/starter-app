from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    mock_pool = MagicMock()
    mock_pool.close = AsyncMock()
    with patch(
        "backend.main.asyncpg.create_pool",
        new_callable=AsyncMock,
        return_value=mock_pool,
    ):
        with TestClient(app) as c:
            yield c
