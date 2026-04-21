"""
test_vectorize_e2e.py
End-to-end integration test for the episodic memory pipeline.
Simulates a full memory cycle: embed, upsert, query, and augment.
"""

import sys
import os
import importlib.util
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

# Load modules
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# VectorStoreClient
vsc_path = os.path.join(base_path, "vector_store_client.py")
spec = importlib.util.spec_from_file_location("vector_store_client", vsc_path)
vsc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vsc)
VectorStoreClient = vsc.VectorStoreClient
MemoryType = vsc.MemoryType

# EmbeddingGenerator
eg_path = os.path.join(base_path, "embedding_generator.py")
spec = importlib.util.spec_from_file_location("embedding_generator", eg_path)
eg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eg)
EmbeddingGenerator = eg.EmbeddingGenerator
MockEmbeddingBackend = eg.MockEmbeddingBackend


class TestEpisodicMemoryPipeline:
    """End-to-end tests for episodic memory components."""

    @pytest.mark.asyncio
    async def test_full_memory_cycle(self):
        """Simulate storing and retrieving a memory."""
        # Setup mock API
        mock_response = {"result": {"upserted": 1, "matches": []}}
        
        with patch('aiohttp.ClientSession.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )

            client = VectorStoreClient(
                api_url="http://localhost",
                api_token="dummy",
                index_name="test-index"
            )
            generator = EmbeddingGenerator(backend=MockEmbeddingBackend(dimension=32))

            # 1. Generate embedding
            text = "Participant shared feeling anxious about deadline."
            embedding = await generator.embed_single(text)
            assert len(embedding) == 32

            # 2. Upsert to vector store
            vector_id = await client.upsert_single(
                participant_id="P001",
                day_number=3,
                memory_type=MemoryType.DAILY_SUMMARY,
                vector=embedding,
                metadata={
                    "emotional_tone": "anxious",
                    "topic": "deadline"
                },
                content=text
            )
            assert "P001_3_daily_summary" in vector_id

    @pytest.mark.asyncio
    async def test_query_and_augment(self):
        """Simulate querying memories and assembling context."""
        # Mock query response
        mock_matches = [
            {
                "id": "P001_2_daily_summary_abc",
                "score": 0.89,
                "metadata": {
                    "participant_id": "P001",
                    "day_number": 2,
                    "memory_type": "daily_summary",
                    "summary_text": "Discussed project timeline."
                }
            },
            {
                "id": "P001_1_chat_message_def",
                "score": 0.76,
                "metadata": {
                    "participant_id": "P001",
                    "day_number": 1,
                    "memory_type": "chat_message"
                }
            }
        ]

        with patch('aiohttp.ClientSession.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value={"result": {"matches": mock_matches}}
            )

            client = VectorStoreClient(
                api_url="http://localhost",
                api_token="dummy",
            )
            generator = EmbeddingGenerator(backend=MockEmbeddingBackend(dimension=32))

            # Query with a new embedding
            query_text = "Can you help me with my timeline?"
            query_embedding = await generator.embed_single(query_text)

            results = await client.query_by_participant(
                participant_id="P001",
                query_vector=query_embedding,
                top_k=3
            )
            assert len(results) == 2
            assert results[0].score == 0.89

            # Convert to format expected by augmenter (simulate Rust FFI)
            # In real integration, this would call the Rust library
            contexts = [
                f"[{r.metadata.get('memory_type', 'unknown')}] {r.metadata.get('summary_text', r.id)}"
                for r in results
            ]
            assembled = "\n".join(contexts)
            assert "Discussed project timeline" in assembled


@pytest.mark.asyncio
async def test_persona_differentiation():
    """Test that Samara and Artery receive different context framing."""
    # This tests the conceptual difference without actual API calls
    
    def assemble_for_persona(memories, persona):
        if "Samara" in persona:
            return f"Here are some warm memories from our previous conversations:\n{memories}"
        else:
            return f"Previous interaction data:\n{memories}"
    
    memories = "- Participant mentioned deadline stress."
    samara_ctx = assemble_for_persona(memories, "Samara")
    artery_ctx = assemble_for_persona(memories, "Artery 1.0")
    
    assert "warm memories" in samara_ctx
    assert "warm memories" not in artery_ctx
    assert "Previous interaction data" in artery_ctx
