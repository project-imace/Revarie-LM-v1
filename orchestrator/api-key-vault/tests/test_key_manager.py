import pytest
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from key_manager import APIKeyVault, KeyStatus

@pytest.mark.asyncio
async def test_register_and_retrieve():
    vault = APIKeyVault()
    vault.register_keys("groq", "model-a", ["k1", "k2"])
    key = await vault.get_key("groq", "model-a")
    assert key.key in ["k1", "k2"]

@pytest.mark.asyncio
async def test_rate_limit_causes_skip():
    vault = APIKeyVault()
    vault.register_keys("groq", "model-a", ["k1", "k2"])
    key1 = await vault.get_key("groq", "model-a")
    await vault.record_failure(key1, is_rate_limit=True)
    key2 = await vault.get_key("groq", "model-a")
    assert key2.key != key1.key
