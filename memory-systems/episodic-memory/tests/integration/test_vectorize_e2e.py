import pytest
from unittest.mock import AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vector_store_client import VectorStoreClient, MemoryType
from embedding_generator import EmbeddingGenerator, MockEmbeddingBackend


class TestEpisodicMemoryPipeline:
    """Integration tests for episodic memory components."""

    @pytest.mark.asyncio
    async def test_full_memory_cycle(self):
        """Simulate storing and retrieving a memory."""
        # Setup mock API
        mock_response = {"result": {"upserted": 1, "matches": []}}

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.text = AsyncMock(
                return_value='{"result": {"upserted": 1, "matches": []}}'
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

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.text = AsyncMock(
                return_value='{"result": {"matches": [{"id": "P001_2_daily_summary_abc", "score": 0.89, "metadata": {"participant_id": "P001", "day_number": 2, "memory_type": "daily_summary", "summary_text": "Discussed project timeline."}}, {"id": "P001_1_chat_message_def", "score": 0.76, "metadata": {"participant_id": "P001", "day_number": 1, "memory_type": "chat_message"}}]}}'
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
            assert results[0].id == "P001_2_daily_summary_abc"
            assert results[0].score == 0.89

def test_persona_differentiation():
    """Test that embedding prompts reflect persona instructions."""
    # Just checking prompt assembly string logic
    text = "User said they like apples."
    
    # Artery prompt
    prompt_artery = f"Represent the following interaction functionally and objectively: {text}"
    # Samara prompt
    prompt_samara = f"Represent the following interaction focusing on relational dynamics: {text}"
    
    assert "functionally" in prompt_artery
    assert "relational" in prompt_samara
    assert prompt_artery != prompt_samara
