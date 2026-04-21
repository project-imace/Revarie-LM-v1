"""
test_router_fallback.py – Property tests for router fallback behavior.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from hypothesis import given, strategies as st
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from reasoning_router import ReasoningRouter
from social_router import SocialRouter
from memory_router import MemoryRouter
from safety_router import SafetyRouter, SafetyTask


class TestRouterFallback:
    """
    Property: Routers always return a valid model even when all keys are rate-limited.
    """

    @given(st.sampled_from(["reasoning", "social", "memory", "safety"]))
    def test_router_always_returns_model(self, router_type):
        async def run_async(rt):
            mock_vault = AsyncMock()
            mock_vault.get_key.return_value = None

            if rt == "reasoning":
                router = ReasoningRouter(mock_vault)
                route = await router.route("test prompt")
            elif rt == "social":
                router = SocialRouter(mock_vault, persona="samara")
                route = await router.route("test")
            elif rt == "memory":
                router = MemoryRouter(mock_vault)
                route = await router.route({"task_type": "summary"})
            else:  # safety
                router = SafetyRouter(mock_vault)
                route = await router.route(SafetyTask.FULL_GUARD)

            assert route.provider is not None
            assert route.model is not None
        
        asyncio.run(run_async(router_type))

    @pytest.mark.asyncio
    async def test_fallback_chain_never_exceeds_limit(self):
        mock_vault = AsyncMock()
        mock_key = MagicMock()
        mock_key.is_available.return_value = True
        mock_vault.get_key.return_value = mock_key

        router = ReasoningRouter(mock_vault)
        route = await router.route("complex analysis requiring deep thought")

        # Property: Fallback chain is bounded (max 3 for reasoning)
        assert len(route.fallback_chain) <= 3

    @pytest.mark.asyncio
    async def test_temperature_in_valid_range(self):
        mock_vault = AsyncMock()
        mock_key = MagicMock()
        mock_key.is_available.return_value = True
        mock_vault.get_key.return_value = mock_key

        router = SocialRouter(mock_vault, persona="samara")
        route = await router.route("Hello")

        # Property: Temperature always in [0.0, 1.0]
        assert 0.0 <= route.temperature <= 1.0
