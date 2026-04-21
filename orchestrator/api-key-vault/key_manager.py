"""
key_manager.py – Orchestrator: API Key Vault

Manages multiple API keys across providers (Groq, Cerebras, Gemini) with
round‑robin load balancing, exponential backoff on rate limits, and health
tracking to prevent overuse of rate‑limited keys.

Theoretical Foundations:
- Rate limiting and queuing theory for distributed systems
- Exponential backoff algorithm (binary exponential backoff for collision avoidance)
- Circuit breaker pattern for fault tolerance
"""

import asyncio
import time
import random
from typing import Dict, List, Optional, Tuple, Any, Deque
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KeyStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    RATE_LIMITED = "rate_limited"
    FAILED = "failed"


@dataclass
class APIKey:
    """Represents a single API key with its state."""
    key: str
    provider: str
    model: str
    status: KeyStatus = KeyStatus.HEALTHY
    last_used: float = 0.0
    rate_limit_until: float = 0.0
    failure_count: int = 0
    success_count: int = 0
    total_calls: int = 0
    avg_latency: float = 0.0

    def is_available(self) -> bool:
        """Check if key is currently usable."""
        if self.status == KeyStatus.FAILED:
            return False
        if self.status == KeyStatus.RATE_LIMITED:
            if time.time() < self.rate_limit_until:
                return False
            # Rate limit expired, reset to degraded
            self.status = KeyStatus.DEGRADED
        return True

    def record_success(self, latency: float):
        self.success_count += 1
        self.total_calls += 1
        self.avg_latency = (self.avg_latency * (self.total_calls - 1) + latency) / self.total_calls
        self.failure_count = 0
        self.status = KeyStatus.HEALTHY

    def record_failure(self, is_rate_limit: bool = False):
        self.failure_count += 1
        self.total_calls += 1
        if is_rate_limit:
            self.status = KeyStatus.RATE_LIMITED
            # Exponential backoff: 1s, 2s, 4s, 8s... capped at 60s
            backoff = min(60, 2 ** (self.failure_count - 1))
            self.rate_limit_until = time.time() + backoff
        elif self.failure_count >= 3:
            self.status = KeyStatus.FAILED


@dataclass
class KeyPool:
    """Manages a pool of API keys for a specific provider‑model combination."""
    provider: str
    model: str
    keys: Deque[APIKey] = field(default_factory=deque)
    index: int = 0
    health_check_interval: float = 60.0
    last_health_check: float = 0.0

    def add_key(self, key: str):
        self.keys.append(APIKey(key=key, provider=self.provider, model=self.model))

    def get_next_key(self) -> Optional[APIKey]:
        """Get next available key using round‑robin with health filtering."""
        if not self.keys:
            return None

        original_index = self.index
        while True:
            key = self.keys[self.index % len(self.keys)]
            self.index = (self.index + 1) % len(self.keys)

            if key.is_available():
                return key

            if self.index == original_index:
                break

        # If all keys are unavailable, return the least recently failed
        available_keys = [k for k in self.keys if k.status != KeyStatus.FAILED]
        if available_keys:
            return min(available_keys, key=lambda k: k.rate_limit_until)
        return None

    def health_check(self):
        """Periodic health check to reset degraded keys."""
        now = time.time()
        if now - self.last_health_check < self.health_check_interval:
            return
        self.last_health_check = now

        for key in self.keys:
            if key.status == KeyStatus.RATE_LIMITED and key.rate_limit_until < now:
                key.status = KeyStatus.DEGRADED
            elif key.status == KeyStatus.FAILED and key.failure_count > 0:
                # Gradual recovery
                key.failure_count = max(0, key.failure_count - 1)
                if key.failure_count == 0:
                    key.status = KeyStatus.DEGRADED


class APIKeyVault:
    """
    Central vault managing all API keys across providers.
    """

    def __init__(self):
        self.pools: Dict[str, KeyPool] = {}
        self._lock = asyncio.Lock()

    def register_keys(self, provider: str, model: str, keys: List[str]):
        """Register a pool of keys for a specific provider‑model combination."""
        pool_id = f"{provider}:{model}"
        if pool_id not in self.pools:
            self.pools[pool_id] = KeyPool(provider=provider, model=model)

        for key in keys:
            self.pools[pool_id].add_key(key)

        logger.info(f"Registered {len(keys)} keys for {pool_id}")

    async def get_key(self, provider: str, model: str) -> Optional[APIKey]:
        """Get next available key with round‑robin and health filtering."""
        async with self._lock:
            pool_id = f"{provider}:{model}"
            if pool_id not in self.pools:
                logger.error(f"No key pool found for {pool_id}")
                return None

            pool = self.pools[pool_id]
            pool.health_check()
            return pool.get_next_key()

    async def record_success(self, key: APIKey, latency: float):
        """Record successful API call."""
        async with self._lock:
            key.record_success(latency)

    async def record_failure(self, key: APIKey, is_rate_limit: bool = False):
        """Record failed API call."""
        async with self._lock:
            key.record_failure(is_rate_limit)

    def get_pool_stats(self) -> Dict[str, Any]:
        """Return statistics for all key pools."""
        stats = {}
        for pool_id, pool in self.pools.items():
            pool_stats = {
                "provider": pool.provider,
                "model": pool.model,
                "total_keys": len(pool.keys),
                "healthy": sum(1 for k in pool.keys if k.status == KeyStatus.HEALTHY),
                "degraded": sum(1 for k in pool.keys if k.status == KeyStatus.DEGRADED),
                "rate_limited": sum(1 for k in pool.keys if k.status == KeyStatus.RATE_LIMITED),
                "failed": sum(1 for k in pool.keys if k.status == KeyStatus.FAILED),
            }
            stats[pool_id] = pool_stats
        return stats

    def health_check_all(self):
        """Run health check on all pools."""
        for pool in self.pools.values():
            pool.health_check()


# =============================================================================
# Exponential Backoff Retry Wrapper
# =============================================================================
class ExponentialBackoff:
    """
    Exponential backoff retry mechanism for API calls.
    """

    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0, jitter: bool = True):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter

    async def retry(
        self,
        func,
        *args,
        max_retries: int = 5,
        retry_on: Tuple[type, ...] = (Exception,),
        **kwargs,
    ):
        """Execute function with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except retry_on as e:
                if attempt == max_retries - 1:
                    raise

                delay = min(self.max_delay, self.base_delay * (2 ** attempt))
                if self.jitter:
                    delay = delay * (0.5 + random.random())

                logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay:.2f}s: {e}")
                await asyncio.sleep(delay)
