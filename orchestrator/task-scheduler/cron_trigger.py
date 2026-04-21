"""
cron_trigger.py – Task Scheduler: Cron Trigger

Triggers external scheduled tasks including:
- Kaggle nightly consolidation notebook execution
- Hugging Face Space health checks and keepalive pings
- D1 database maintenance tasks

Designed to be called by external cron services (e.g., cron-job.org).
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CronTrigger:
    """
    Handles scheduled task execution for Revarie LM v1.0.
    """

    def __init__(self):
        self.kaggle_api_key = os.environ.get("KAGGLE_KEY")
        self.kaggle_username = os.environ.get("KAGGLE_USERNAME")
        self.hf_space_url = os.environ.get("HF_SPACE_URL", "https://revarie-lm-v1-engine.hf.space")
        self.health_endpoint = f"{self.hf_space_url}/health"

    async def trigger_kaggle_notebook(self, notebook_slug: str = "revarie-nightly-consolidation") -> Dict[str, Any]:
        """
        Trigger a Kaggle notebook execution via Kaggle API.

        Args:
            notebook_slug: The Kaggle notebook identifier

        Returns:
            API response as dictionary
        """
        if not self.kaggle_api_key or not self.kaggle_username:
            logger.error("Kaggle credentials not configured")
            return {"error": "Kaggle credentials missing"}

        url = f"https://www.kaggle.com/api/v1/kernels/push"
        
        # Kaggle API authentication
        auth = aiohttp.BasicAuth(self.kaggle_username, self.kaggle_api_key)

        payload = {
            "slug": notebook_slug,
            "newTitle": f"Revarie Nightly Consolidation - {datetime.utcnow().date()}",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, auth=auth, json=payload) as resp:
                    data = await resp.json()
                    if resp.status == 200:
                        logger.info(f"Successfully triggered Kaggle notebook: {notebook_slug}")
                        return {"success": True, "data": data}
                    else:
                        logger.error(f"Kaggle API error: {resp.status} - {data}")
                        return {"success": False, "error": data}
        except Exception as e:
            logger.error(f"Failed to trigger Kaggle notebook: {e}")
            return {"success": False, "error": str(e)}

    async def ping_huggingface_space(self) -> Dict[str, Any]:
        """
        Ping the Hugging Face Space health endpoint to keep it alive.

        HF Spaces on free tier sleep after 48 hours of inactivity.
        This ping resets the inactivity timer.

        Returns:
            Health check result
        """
        try:
            async with aiohttp.ClientSession() as session:
                start = time.time()
                async with session.get(self.health_endpoint, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    latency_ms = (time.time() - start) * 1000
                    data = await resp.json() if resp.status == 200 else await resp.text()

                    logger.info(f"HF Space ping: {resp.status} ({latency_ms:.0f}ms)")
                    return {
                        "success": resp.status == 200,
                        "status_code": resp.status,
                        "latency_ms": latency_ms,
                        "response": data if isinstance(data, dict) else {"text": data[:200]},
                    }
        except asyncio.TimeoutError:
            logger.warning("HF Space ping timeout")
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.error(f"HF Space ping failed: {e}")
            return {"success": False, "error": str(e)}

    async def run_nightly_maintenance(self) -> Dict[str, Any]:
        """
        Execute full nightly maintenance routine.

        Returns:
            Summary of executed tasks
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "hf_ping": None,
            "kaggle_trigger": None,
        }

        # 1. Ping HF Space to keep it alive
        logger.info("Starting nightly maintenance...")
        results["hf_ping"] = await self.ping_huggingface_space()

        # 2. Trigger Kaggle consolidation notebook (only if credentials exist)
        if self.kaggle_api_key:
            results["kaggle_trigger"] = await self.trigger_kaggle_notebook()
        else:
            logger.info("Skipping Kaggle trigger (no credentials)")

        logger.info(f"Nightly maintenance complete: {results}")
        return results
