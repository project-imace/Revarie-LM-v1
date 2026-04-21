import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from cerebras_client import CerebrasClient

@pytest.mark.asyncio
async def test_qwen_model_used():
    mock_vault = AsyncMock()
    mock_key = MagicMock()
    mock_key.key = "test-key"
    mock_vault.get_key.return_value = mock_key

    client = CerebrasClient(mock_vault)

    mock_response = {
        "choices": [{"message": {"content": "Reasoned response"}, "finish_reason": "stop"}],
        "model": "qwen-3-235b",
        "usage": {}
    }

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value.status = 200
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)

        response = await client.chat(
            [{"role": "user", "content": "Complex question"}],
            "qwen-3-235b-a22b-instruct-2507"
        )

    assert "Reasoned" in response.text
