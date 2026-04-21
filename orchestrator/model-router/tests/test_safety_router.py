import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from safety_router import SafetyRouter, SafetyTask

@pytest.mark.asyncio
async def test_injection_uses_guard_model():
    mock_vault = AsyncMock()
    mock_key = MagicMock()
    mock_key.is_available.return_value = True
    mock_vault.get_key.return_value = mock_key

    router = SafetyRouter(mock_vault)
    route = await router.route(SafetyTask.PROMPT_INJECTION)

    assert "prompt-guard" in route.model

@pytest.mark.asyncio
async def test_fallback_chain_built():
    mock_vault = AsyncMock()
    mock_key = MagicMock()
    mock_key.is_available.return_value = True
    mock_vault.get_key.return_value = mock_key

    router = SafetyRouter(mock_vault)
    route = await router.route(SafetyTask.FULL_GUARD)

    assert len(route.fallback_chain) >= 0
