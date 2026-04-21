import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from memory_router import MemoryRouter, MemoryTask

@pytest.mark.asyncio
async def test_real_time_uses_fast_model():
    mock_vault = AsyncMock()
    mock_key = MagicMock()
    mock_key.is_available.return_value = True
    mock_vault.get_key.return_value = mock_key

    router = MemoryRouter(mock_vault)
    route = await router.route({"task_type": "real_time_retrieval"})

    assert route.priority_latency is True
    assert route.model == "llama-3.1-8b-instant"

@pytest.mark.asyncio
async def test_consolidation_uses_quality_model():
    mock_vault = AsyncMock()
    mock_key = MagicMock()
    mock_key.is_available.return_value = True
    mock_vault.get_key.return_value = mock_key

    router = MemoryRouter(mock_vault)
    route = await router.route({"task_type": "consolidation"})

    assert route.priority_latency is False
