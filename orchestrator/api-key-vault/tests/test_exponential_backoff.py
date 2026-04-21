import pytest
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from exponential_backoff import exponential_backoff, RateLimitError

@pytest.mark.asyncio
async def test_retry_succeeds():
    calls = 0
    @exponential_backoff(max_retries=3, base_delay=0.01)
    async def flaky():
        nonlocal calls
        calls += 1
        if calls < 2:
            raise RateLimitError()
        return "ok"
    assert await flaky() == "ok"
    assert calls == 2
