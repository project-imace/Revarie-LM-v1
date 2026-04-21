import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from memory_systems.memory_consolidation.consolidation_orchestrator import ConsolidationOrchestrator

@pytest.mark.asyncio
async def test_orchestrator_initialization():
    mock_d1 = AsyncMock()
    mock_vs = AsyncMock()
    mock_emb = AsyncMock()
    orch = ConsolidationOrchestrator(mock_d1, mock_vs, mock_emb)
    assert orch.max_concurrent == 5
