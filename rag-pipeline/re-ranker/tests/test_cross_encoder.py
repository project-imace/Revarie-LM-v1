import pytest
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from cross_encoder import CrossEncoderReranker
from dataclasses import dataclass, field
from typing import Dict, Any
@dataclass
class MockRetrievalResult:
    id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@pytest.mark.asyncio
async def test_heuristic_rerank():
    reranker = CrossEncoderReranker(use_local=False)
    results = [MockRetrievalResult("1", "cat", 0.9), MockRetrievalResult("2", "dog", 0.8)]
    reranked = await reranker.rerank("cat", results)
    assert reranked[0].id == "1"
