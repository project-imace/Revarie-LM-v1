"""
test_cron_trigger.py – Unit tests for Cron Trigger
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from cron_trigger import CronTrigger


class TestCronTrigger:
    """Test suite for CronTrigger."""

    def test_initialization(self):
        """Test that CronTrigger initializes with environment variables."""
        trigger = CronTrigger()
        assert trigger.hf_space_url is not None
        assert trigger.health_endpoint.endswith("/health")

    @pytest.mark.asyncio
    async def test_ping_huggingface_space_success(self):
        """Test successful HF Space ping."""
        trigger = CronTrigger()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "healthy"})

        with patch("aiohttp.ClientSession.get", return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response)
        )):
            result = await trigger.ping_huggingface_space()

        assert result["success"] is True
        assert result["status_code"] == 200
        assert "latency_ms" in result

    @pytest.mark.asyncio
    async def test_ping_huggingface_space_failure(self):
        """Test HF Space ping failure."""
        trigger = CronTrigger()

        with patch("aiohttp.ClientSession.get", side_effect=asyncio.TimeoutError()):
            result = await trigger.ping_huggingface_space()

        assert result["success"] is False
        assert result["error"] == "timeout"

    @pytest.mark.asyncio
    async def test_trigger_kaggle_missing_credentials(self):
        """Test Kaggle trigger when credentials are missing."""
        trigger = CronTrigger()
        trigger.kaggle_api_key = None

        result = await trigger.trigger_kaggle_notebook()
        assert result["error"] == "Kaggle credentials missing"

    @pytest.mark.asyncio
    async def test_trigger_kaggle_success(self):
        """Test successful Kaggle notebook trigger."""
        trigger = CronTrigger()
        trigger.kaggle_username = "testuser"
        trigger.kaggle_api_key = "testkey"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"ref": "kernel-123"})

        with patch("aiohttp.ClientSession.post", return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response)
        )):
            result = await trigger.trigger_kaggle_notebook("test-notebook")

        assert result["success"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_run_nightly_maintenance(self):
        """Test full nightly maintenance routine."""
        trigger = CronTrigger()
        trigger.kaggle_api_key = "testkey"
        trigger.kaggle_username = "testuser"

        # Mock both ping and kaggle calls
        with patch.object(trigger, "ping_huggingface_space", return_value={"success": True}) as mock_ping, \
             patch.object(trigger, "trigger_kaggle_notebook", return_value={"success": True}) as mock_kaggle:

            result = await trigger.run_nightly_maintenance()

        assert result["hf_ping"] is not None
        assert result["kaggle_trigger"] is not None
        assert "timestamp" in result
        mock_ping.assert_called_once()
        mock_kaggle.assert_called_once()


class TestCronTriggerIntegration:
    """Integration-style tests with actual async execution."""

    @pytest.mark.asyncio
    async def test_maintenance_without_kaggle(self):
        """Test maintenance runs even without Kaggle credentials."""
        trigger = CronTrigger()
        trigger.kaggle_api_key = None

        with patch.object(trigger, "ping_huggingface_space", return_value={"success": True}):
            result = await trigger.run_nightly_maintenance()

        assert result["hf_ping"]["success"] is True
        assert result["kaggle_trigger"] is None  # Skipped


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
