import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from groq_client import GroqClient, GroqResponse

@pytest.mark.asyncio
async def test_chat_success():
    mock_vault = AsyncMock()
    mock_key = MagicMock()
    mock_key.key = "test-key"
    mock_vault.get_key.return_value = mock_key

    client = GroqClient(mock_vault)

    mock_response = {
        "choices": [{"message": {"content": "Hello!"}, "finish_reason": "stop"}],
        "model": "test-model",
        "usage": {"total_tokens": 10}
    }

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value.status = 200
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)

        response = await client.chat([{"role": "user", "content": "Hi"}], "test-model")

    assert response.text == "Hello!"
    mock_vault.record_success.assert_called_once()

@pytest.mark.asyncio
async def test_rate_limit_triggers_retry():
    mock_vault = AsyncMock()
    mock_key = MagicMock()
    mock_key.key = "test-key"
    mock_vault.get_key.return_value = mock_key

    client = GroqClient(mock_vault)
    client.timeout = aiohttp.ClientTimeout(total=1)

    call_count = 0
    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            resp = MagicMock()
            resp.status = 429
            return resp
        else:
            resp = MagicMock()
            resp.status = 200
            resp.json = AsyncMock(return_value={
                "choices": [{"message": {"content": "Success"}, "finish_reason": "stop"}]
            })
            return resp

    with patch("aiohttp.ClientSession.post", new=mock_post):
        response = await client.chat([{"role": "user", "content": "Hi"}], "test-model", retries=2)

    assert response.text == "Success"
    assert call_count == 2
    mock_vault.record_failure.assert_called()
