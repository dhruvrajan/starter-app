import pytest

from backend.worker import _process_message


@pytest.mark.asyncio
async def test_process_message(capsys):
    await _process_message("hello")
    assert "hello" in capsys.readouterr().out
