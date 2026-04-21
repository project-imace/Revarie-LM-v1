"""
gemini_client.py – Provider Client: Gemini

Manages 2 Gemini API keys for premium fallback:
- gemini-2.5-flash (primary premium)
- gemini-2.5-flash-lite (efficient premium)

Use sparingly – low RPM limits on free tier.
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
class GeminiResponse:
    """Standardized response from Gemini API."""
    text: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""
    latency_ms: float = 0.0
    key_used: str = ""


class GeminiClient:
    """
    Gemini API client – use sparingly due to low free tier limits.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, key_vault):
        self.key_vault = key_vault
        self.timeout = aiohttp.ClientTimeout(total=60)

        self.model_configs = {
            "gemini-2.5-flash": {"max_tokens": 2048, "default_temperature": 0.7},
            "gemini-2.5-flash-lite": {"max_tokens": 1024, "default_temperature": 0.7},
        }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gemini-2.5-flash",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        retries: int = 2,  # Fewer retries due to low limits
    ) -> GeminiResponse:
        """
        Send chat request to Gemini. Use sparingly.
        """
        config = self.model_configs.get(model, {"max_tokens": 1024, "default_temperature": 0.7})
        temperature = temperature if temperature is not None else config["default_temperature"]
        max_tokens = max_tokens or config["max_tokens"]

        # Convert messages to Gemini format
        gemini_messages = self._convert_messages(messages)

        last_error = None

        for attempt in range(retries):
            key = await self.key_vault.get_key("gemini", model)
            if not key:
                logger.error(f"No available Gemini key for {model}")
                await asyncio.sleep(2 ** attempt)
                continue

            start_time = time.time()

            try:
                url = f"{self.BASE_URL}/{model}:generateContent?key={key.key}"

                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    payload = {
                        "contents": gemini_messages,
                        "generationConfig": {
                            "temperature": temperature,
                            "maxOutputTokens": max_tokens,
                        },
                    }

                    async with session.post(url, json=payload) as resp:
                        latency_ms = (time.time() - start_time) * 1000

                        if resp.status == 200:
                            data = await resp.json()
                            await self.key_vault.record_success(key, latency_ms)

                            text = data["candidates"][0]["content"]["parts"][0]["text"]
                            return GeminiResponse(
                                text=text,
                                model=model,
                                usage=data.get("usageMetadata", {}),
                                finish_reason=data["candidates"][0].get("finishReason", ""),
                                latency_ms=latency_ms,
                                key_used=key.key[:8] + "...",
                            )

                        elif resp.status == 429:
                            await self.key_vault.record_failure(key, is_rate_limit=True)
                            logger.warning(f"Gemini rate limited for {model}")
                            await asyncio.sleep(10)  # Gemini rate limits are strict
                            continue

                        else:
                            error_text = await resp.text()
                            await self.key_vault.record_failure(key, is_rate_limit=False)
                            last_error = f"HTTP {resp.status}: {error_text}"
                            logger.error(f"Gemini API error: {last_error}")
                            continue

            except Exception as e:
                await self.key_vault.record_failure(key, is_rate_limit=False)
                last_error = str(e)
                logger.error(f"Gemini exception: {e}")
                continue

        raise Exception(f"Gemini API failed after {retries} retries: {last_error}")

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict]:
        """Convert OpenAI format messages to Gemini format."""
        gemini_msgs = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_msgs.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        return gemini_msgs

    async def chat_simple(self, prompt: str, model: str = "gemini-2.5-flash", **kwargs) -> str:
        """Simple chat with single user message."""
        response = await self.chat([{"role": "user", "content": prompt}], model, **kwargs)
        return response.text
