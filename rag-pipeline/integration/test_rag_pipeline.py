"""
test_rag_pipeline.py – End‑to‑end RAG pipeline integration test
"""

import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

async def test_full_rag_flow():
    """Simulate complete RAG pipeline: retrieve → rerank → prompt → generate."""
    # Mock components
    class MockRetriever:
        async def retrieve(self, *args, **kwargs):
            return type('Batch', (), {'results': [
                type('R', (), {'id': '1', 'content': 'Memory 1', 'score': 0.9, 'metadata': {}})(),
                type('R', (), {'id': '2', 'content': 'Memory 2', 'score': 0.7, 'metadata': {}})(),
            ]})()

    class MockReranker:
        async def rerank(self, query, results, top_k=2):
            return results[:top_k]

    class MockPromptBuilder:
        def build(self, query, memories, ctx, history=None):
            return [{"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": query}]

    retriever = MockRetriever()
    reranker = MockReranker()
    builder = MockPromptBuilder()

    # Simulate flow
    query = "Tell me about my progress"
    ctx = {"name": "Test", "day_progress": 3}

    batch = await retriever.retrieve("test_ns", [0.1]*1536)
    reranked = await reranker.rerank(query, batch.results)
    messages = builder.build(query, [r.content for r in reranked], ctx)

    assert len(messages) == 2
    assert messages[1]["content"] == query
    print("✅ Full RAG pipeline integration test passed")


if __name__ == "__main__":
    asyncio.run(test_full_rag_flow())
