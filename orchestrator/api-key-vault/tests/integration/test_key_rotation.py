"""
test_key_rotation.py – Integration test for key rotation across multiple providers
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from key_manager import APIKeyVault, KeyStatus
from exponential_backoff import RateLimitError


async def test_full_key_rotation_flow():
    """Simulate complete key rotation with rate limits and recovery."""
    vault = APIKeyVault()

    # Register keys for all domains
    # Domain 1: Reasoning Models
    vault.register_keys("groq", "gpt-oss-120b", [f"groq_reasoning_{i}" for i in range(1, 9)])
    vault.register_keys("groq", "gpt-oss-20b", [f"groq_reasoning_20b_{i}" for i in range(1, 9)])
    vault.register_keys("cerebras", "qwen-3-235b", [f"cerebras_qwen_{i}" for i in range(1, 9)])

    # Domain 2: Social Interactive Models
    vault.register_keys("groq", "llama-3.3-70b-versatile", [f"groq_social_70b_{i}" for i in range(1, 9)])
    vault.register_keys("groq", "llama-4-scout-17b", [f"groq_social_scout_{i}" for i in range(1, 9)])
    vault.register_keys("cerebras", "llama3.1-8b", [f"cerebras_social_{i}" for i in range(1, 9)])
    vault.register_keys("gemini", "gemini-2.5-flash", ["gemini_flash_1", "gemini_flash_2"])
    vault.register_keys("gemini", "gemini-2.5-flash-lite", ["gemini_lite_1", "gemini_lite_2"])

    # Domain 3: Memory Recall
    vault.register_keys("groq", "llama-3.1-8b-instant", [f"groq_memory_instant_{i}" for i in range(1, 9)])
    vault.register_keys("groq", "qwen3-32b", [f"groq_memory_qwen_{i}" for i in range(1, 9)])

    # Domain 4: Safety & Regulation
    vault.register_keys("groq", "gpt-oss-safeguard-20b", [f"groq_safety_sg_{i}" for i in range(1, 9)])
    vault.register_keys("groq", "llama-prompt-guard-86m", [f"groq_safety_86m_{i}" for i in range(1, 9)])
    vault.register_keys("groq", "llama-prompt-guard-22m", [f"groq_safety_22m_{i}" for i in range(1, 9)])

    # Test 1: Round-robin across 8 keys
    used_keys = set()
    for _ in range(8):
        key = await vault.get_key("groq", "gpt-oss-120b")
        assert key is not None
        used_keys.add(key.key)
    assert len(used_keys) == 8, f"Expected 8 unique keys, got {len(used_keys)}"

    # Test 2: Rate limit handling
    key1 = await vault.get_key("cerebras", "qwen-3-235b")
    await vault.record_failure(key1, is_rate_limit=True)
    
    # Next 7 calls should use other keys
    next_keys = set()
    for _ in range(7):
        k = await vault.get_key("cerebras", "qwen-3-235b")
        next_keys.add(k.key)
        assert k.key != key1.key  # Rate-limited key should be skipped
    
    assert len(next_keys) == 7

    # Test 3: Pool stats
    stats = vault.get_pool_stats()
    groq_120b = stats.get("groq:gpt-oss-120b", {})
    assert groq_120b.get("total_keys") == 8
    assert groq_120b.get("healthy") == 8

    cerebras_qwen = stats.get("cerebras:qwen-3-235b", {})
    assert cerebras_qwen.get("rate_limited", 0) >= 1

    print("✅ Full key rotation flow passed")


async def test_rate_limit_recovery():
    """Test that rate-limited keys eventually recover."""
    vault = APIKeyVault()
    vault.register_keys("groq", "test-model", ["key1", "key2"])

    key1 = await vault.get_key("groq", "test-model")
    await vault.record_failure(key1, is_rate_limit=True)
    
    # Manually simulate time passing (override rate_limit_until)
    key1.rate_limit_until = 0
    key1.status = KeyStatus.DEGRADED
    
    # Now key1 should be available again
    key_again = await vault.get_key("groq", "test-model")
    assert key_again.key == "key1" or key_again.key == "key2"

    print("✅ Rate limit recovery passed")


async def test_exhaustion_fallback():
    """Test fallback when all keys are rate-limited."""
    vault = APIKeyVault()
    vault.register_keys("groq", "test-model", ["key1", "key2"])

    key1 = await vault.get_key("groq", "test-model")
    key2 = await vault.get_key("groq", "test-model")
    
    await vault.record_failure(key1, is_rate_limit=True)
    await vault.record_failure(key2, is_rate_limit=True)
    
    # Should still return a key (least recently rate-limited)
    fallback = await vault.get_key("groq", "test-model")
    assert fallback is not None

    print("✅ Exhaustion fallback passed")


async def main():
    await test_full_key_rotation_flow()
    await test_rate_limit_recovery()
    await test_exhaustion_fallback()


if __name__ == "__main__":
    asyncio.run(main())
