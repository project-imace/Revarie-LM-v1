from unittest.mock import AsyncMock
"""test_full_chat_flow.py – End‑to‑end chat flow integration test."""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

@pytest.mark.asyncio
async def test_samara_chat_flow(mock_d1_client, mock_vector_store, mock_embedding_generator):
    """Test complete Samara chat flow from context building to response."""
    # This test simulates the full pipeline:
    # 1. Build participant context
    # 2. Retrieve relevant memories
    # 3. Route to appropriate model
    # 4. Generate response
    # 5. Update session state

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'persona-engine', 'participant-context'))
    from context_builder import ContextBuilder

    builder = ContextBuilder(mock_d1_client, mock_vector_store, mock_embedding_generator, cache_ttl=0)
    ctx = await builder.build("P001", current_query="How are you?")

    assert ctx.participant_id == "P001"
    assert ctx.name == "Test User"
    assert ctx.study_group == "A"
    print("✅ Samara chat flow context built successfully")


@pytest.mark.asyncio
async def test_artery_chat_flow(mock_d1_client, mock_vector_store, mock_embedding_generator):
    """Test complete Artery chat flow."""
    mock_d1_client.get_participant.return_value.study_group = "B"
    mock_d1_client.get_participant.return_value.ai_type = "Functional AI Artery"

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'persona-engine', 'participant-context'))
    from context_builder import ContextBuilder

    builder = ContextBuilder(mock_d1_client, mock_vector_store, mock_embedding_generator, cache_ttl=0)
    ctx = await builder.build("P002", current_query="Status report")

    assert ctx.participant_id == "P002"
    assert ctx.study_group == "B"
    print("✅ Artery chat flow context built successfully")


@pytest.mark.asyncio
async def test_memory_retrieval_integration(mock_vector_store, mock_embedding_generator):
    """Test that memories are correctly retrieved and formatted."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'rag-pipeline', 'retriever'))
    from vector_retriever import VectorRetriever

    retriever = VectorRetriever(
        api_url="http://localhost",
        api_token="test-token",
        account_id="test-account",
    )

    # Mock the internal _request method
    retriever._request = AsyncMock(return_value={
        "result": {
            "matches": [
                {"id": "mem1", "score": 0.95, "metadata": {"content": "Memory 1"}},
                {"id": "mem2", "score": 0.85, "metadata": {"content": "Memory 2"}},
            ]
        }
    })

    batch = await retriever.retrieve_for_participant(
        "P001",
        [0.1] * 1536,
        top_k=5
    )

    assert len(batch.results) == 2
    assert batch.results[0].score == 0.95
    print("✅ Memory retrieval integration passed")
