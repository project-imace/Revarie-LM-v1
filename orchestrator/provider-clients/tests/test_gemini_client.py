import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from gemini_client import GeminiClient

@pytest.mark.asyncio
async def test_gemini_format_conversion():
    mock_vault = AsyncMock()
    mock_key = MagicMock()
    mock_key.key = "test-key"
    mock_vault.get_key.return_value = mock_key

    client = GeminiClient(mock_vault)
    messages = [{"role": "user", "content": "Hello"}]
    converted = client._convert_messages(messages)

    assert converted[0]["role"] == "user"
    assert converted[0]["parts"][0]["text"] == "Hello"

@pytest.mark.asyncio
async def test_chat_success():
    mock_vault = AsyncMock()
    mock_key = MagicMock()
    mock_key.key = "test-key"
    mock_vault.get_key.return_value = mock_key

    client = GeminiClient(mock_vault)

    mock_response = {
        "candidates": [{"content": {"parts": [{"text": "Hi there!"}]}, "finishReason": "STOP"}],
        "usageMetadata": {"totalTokenCount": 5}
    }

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value.status = 200
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)

        response = await client.chat([{"role": "user", "content": "Hi"}])

    assert response.text == "Hi there!"
