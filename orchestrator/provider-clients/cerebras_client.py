"""
cerebras_client.py – Provider Client: Cerebras

Manages 8 Cerebras API keys for:
- Reasoning: qwen-3-235b-a22b-instruct-2507 (primary, watch rate limits)
- Social: llama3.1-8b (secondary social)

Note: qwen-235b rate limits easily – use sparingly and with robust fallback.
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CerebrasResponse:
    """Standardized response from Cerebras API."""
    text: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""
    latency_ms: float = 0.0
    key_used: str = ""


class CerebrasClient:
    """
    Cerebras API client with key rotation and rate limit awareness.
    """

    BASE_URL = "https://api.cerebras.ai/v1/chat/completions"

    def __init__(self, key_vault):
        self.key_vault = key_vault
        self.timeout = aiohttp.ClientTimeout(total=90)  # Longer timeout for 235B model

        self.model_configs = {
            "qwen-3-235b-a22b-instruct-2507": {"max_tokens": 4096, "default_temperature": 0.3},
            "llama3.1-8b": {"max_tokens": 1024, "default_temperature": 0.7},
        }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        retries: int = 3,
    ) -> CerebrasResponse:
        """
        Send chat completion request with retry and key rotation.
        """
        config = self.model_configs.get(model, {"max_tokens": 1024, "default_temperature": 0.5})
        temperature = temperature if temperature is not None else config["default_temperature"]
        max_tokens = max_tokens or config["max_tokens"]

        last_error = None

        for attempt in range(retries):
            key = await self.key_vault.get_key("cerebras", model)
            if not key:
                logger.error(f"No available Cerebras key for {model}")
                await asyncio.sleep(2 ** attempt)
                continue

            start_time = time.time()

            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    headers = {
                        "Authorization": f"Bearer {key.key}",
                        "Content-Type": "application/json",
                    }

                    payload = {
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }

                    async with session.post(self.BASE_URL, headers=headers, json=payload) as resp:
                        latency_ms = (time.time() - start_time) * 1000

                        if resp.status == 200:
                            data = await resp.json()
                            await self.key_vault.record_success(key, latency_ms)

                            return CerebrasResponse(
                                text=data["choices"][0]["message"]["content"],
                                model=data.get("model", model),
                                usage=data.get("usage", {}),
                                finish_reason=data["choices"][0].get("finish_reason", ""),
                                latency_ms=latency_ms,
                                key_used=key.key[:8] + "...",
                            )

                        elif resp.status == 429:
                            await self.key_vault.record_failure(key, is_rate_limit=True)
                            logger.warning(f"Cerebras rate limited for {model}, rotating key")
                            # Cerebras rate limits easily – longer backoff
                            await asyncio.sleep(5 * (attempt + 1))
                            continue

                        else:
                            error_text = await resp.text()
                            await self.key_vault.record_failure(key, is_rate_limit=False)
                            last_error = f"HTTP {resp.status}: {error_text}"
                            logger.error(f"Cerebras API error: {last_error}")
                            continue

            except asyncio.TimeoutError:
                await self.key_vault.record_failure(key, is_rate_limit=False)
                last_error = "Timeout"
                logger.warning(f"Cerebras timeout for {model}")
                continue

            except Exception as e:
                await self.key_vault.record_failure(key, is_rate_limit=False)
                last_error = str(e)
                logger.error(f"Cerebras exception: {e}")
                continue

        raise Exception(f"Cerebras API failed after {retries} retries: {last_error}")

    async def chat_simple(self, prompt: str, model: str = "llama3.1-8b", **kwargs) -> str:
        """Simple chat with single user message."""
        response = await self.chat([{"role": "user", "content": prompt}], model, **kwargs)
        return response.text
