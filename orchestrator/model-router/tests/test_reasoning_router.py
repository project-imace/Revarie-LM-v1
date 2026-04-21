import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from reasoning_router import ReasoningRouter, TaskComplexity

@pytest.mark.asyncio
async def test_classify_complexity():
    mock_vault = AsyncMock()
    router = ReasoningRouter(mock_vault)
    assert router.classify_complexity("Why does the sky appear blue?") == TaskComplexity.COMPLEX
    assert router.classify_complexity("Hello") == TaskComplexity.SIMPLE

@pytest.mark.asyncio
async def test_route_selects_model():
    mock_vault = AsyncMock()
    mock_key = MagicMock()
    mock_key.is_available.return_value = True
    mock_vault.get_key.return_value = mock_key

    router = ReasoningRouter(mock_vault)
    route = await router.route("Analyze the implications of quantum entanglement")

    assert route.provider in ["cerebras", "groq"]
    assert route.model is not None
