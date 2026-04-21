import pytest
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from vector_retriever import VectorRetriever, MemoryType, RetrievalResult

@pytest.mark.asyncio
async def test_retriever_initialization():
    retriever = VectorRetriever(api_url="http://test", api_token="token")
    assert retriever.dimension == 1536
    await retriever.close()

def test_retrieval_result_fields():
    r = RetrievalResult(id="x", content="test", score=0.5)
    assert r.id == "x"
    assert r.score == 0.5
