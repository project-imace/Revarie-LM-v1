import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from social_router import SocialRouter, SocialContext

@pytest.mark.asyncio
async def test_classify_context():
    mock_vault = AsyncMock()
    router = SocialRouter(mock_vault, persona="samara")
    assert router.classify_context("Hello there!") == SocialContext.GREETING
    assert router.classify_context("I'm feeling really sad today") == SocialContext.EMOTIONAL_SUPPORT

@pytest.mark.asyncio
async def test_samara_warmer_temperature():
    mock_vault = AsyncMock()
    mock_key = MagicMock()
    mock_key.is_available.return_value = True
    mock_vault.get_key.return_value = mock_key

    samara_router = SocialRouter(mock_vault, persona="samara")
    artery_router = SocialRouter(mock_vault, persona="artery")

    samara_route = await samara_router.route("Hello")
    artery_route = await artery_router.route("Hello")

    assert samara_route.temperature > artery_route.temperature
