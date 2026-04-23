"""
groq_client.py – Provider Client: Groq

Manages 8 Groq API keys across multiple model families:
- Reasoning: openai/gpt-oss-120b, openai/gpt-oss-20b
- Social: llama-3.3-70b-versatile, meta-llama/llama-4-scout-17b-16e-instruct
- Memory: llama-3.1-8b-instant, qwen/qwen3-32b
- Safety: openai/gpt-oss-safeguard-20b, meta-llama/llama-prompt-guard-2-86m, meta-llama/llama-prompt-guard-2-22m

Integrates with APIKeyVault for round‑robin key rotation and rate limit handling.
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class GroqResponse:
    """Standardized response from Groq API."""
    text: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""
    latency_ms: float = 0.0
    key_used: str = ""


class GroqClient:
    """
    Groq API client with automatic key rotation and rate limit handling.
    """

    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, key_vault):
        """
        Args:
            key_vault: APIKeyVault instance for key management
        """
        self.key_vault = key_vault
        self.timeout = aiohttp.ClientTimeout(total=60)

        # Model configurations
        self.model_configs = {
            # Reasoning
            "gpt-oss-120b": {"max_tokens": 4096, "default_temperature": 0.3},
            "gpt-oss-20b": {"max_tokens": 2048, "default_temperature": 0.3},
            # Social
            "llama-3.3-70b-versatile": {"max_tokens": 2048, "default_temperature": 0.7},
            "llama-4-scout-17b": {"max_tokens": 1024, "default_temperature": 0.7},
            # Memory
            "llama-3.1-8b-instant": {"max_tokens": 512, "default_temperature": 0.1},
            "qwen3-32b": {"max_tokens": 1024, "default_temperature": 0.2},
            # Safety
            "gpt-oss-safeguard-20b": {"max_tokens": 512, "default_temperature": 0.0},
            "llama-prompt-guard-86m": {"max_tokens": 256, "default_temperature": 0.0},
            "llama-prompt-guard-22m": {"max_tokens": 256, "default_temperature": 0.0},
        }

    def _normalize_model_name(self, model: str) -> str:
        """Normalize model name for API."""
        if not model.startswith("openai/") and not model.startswith("meta-llama/") and not model.startswith("qwen/"):
            if "gpt-oss" in model:
                return f"openai/{model}"
            elif "llama" in model and "guard" in model:
                return f"meta-llama/{model}"
            elif "qwen" in model:
                return f"qwen/{model}"
        return model

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        retries: int = 3,
    ) -> GroqResponse:
        """
        Send chat completion request with automatic key rotation and retry.
        """
        normalized_model = self._normalize_model_name(model)
        base_model = normalized_model.split("/")[-1]

        config = self.model_configs.get(base_model, {"max_tokens": 1024, "default_temperature": 0.5})
        temperature = temperature if temperature is not None else config["default_temperature"]
        max_tokens = max_tokens or config["max_tokens"]

        last_error = None

        for attempt in range(retries):
            # Get next available key
            key = await self.key_vault.get_key("groq", normalized_model)
            if not key:
                logger.error(f"No available Groq key for {normalized_model}")
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
                        "model": normalized_model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }

                    async with session.post(self.BASE_URL, headers=headers, json=payload) as resp:
                        latency_ms = (time.time() - start_time) * 1000

                        if resp.status == 200:
                            data = await resp.json()
                            await self.key_vault.record_success(key, latency_ms)

                            return GroqResponse(
                                text=data["choices"][0]["message"]["content"],
                                model=data.get("model", normalized_model),
                                usage=data.get("usage", {}),
                                finish_reason=data["choices"][0].get("finish_reason", ""),
                                latency_ms=latency_ms,
                                key_used=key.key[:8] + "...",
                            )

                        elif resp.status == 429:
                            # Rate limited
                            await self.key_vault.record_failure(key, is_rate_limit=True)
                            logger.warning(f"Groq rate limited for {normalized_model}, rotating key")
                            continue

                        else:
                            error_text = await resp.text()
                            await self.key_vault.record_failure(key, is_rate_limit=False)
                            last_error = f"HTTP {resp.status}: {error_text}"
                            logger.error(f"Groq API error: {last_error}")
                            continue

            except asyncio.TimeoutError:
                await self.key_vault.record_failure(key, is_rate_limit=False)
                last_error = "Timeout"
                logger.warning(f"Groq timeout for {normalized_model}")
                continue

            except Exception as e:
                await self.key_vault.record_failure(key, is_rate_limit=False)
                last_error = str(e)
                logger.error(f"Groq exception: {e}")
                continue

        raise Exception(f"Groq API failed after {retries} retries: {last_error}")

    async def chat_simple(self, prompt: str, model: str = "llama-3.3-70b-versatile", **kwargs) -> str:
        """Simple chat with single user message."""
        response = await self.chat([{"role": "user", "content": prompt}], model, **kwargs)
        return response.text

    async def health_check(self) -> Dict[str, Any]:
        """Check health of Groq keys."""
        stats = self.key_vault.get_pool_stats()
        groq_stats = {k: v for k, v in stats.items() if k.startswith("groq:")}
        return {
            "provider": "groq",
            "pools": groq_stats,
        }
