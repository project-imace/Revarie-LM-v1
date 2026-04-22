"""
test_vector_store.py
Unit tests for VectorStoreClient (using mocks).
"""

import sys
import os
import importlib.util
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

# Dynamically load the module
module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "vector_store_client.py")
)
spec = importlib.util.spec_from_file_location("vector_store_client", module_path)
vsc_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vsc_module)

VectorStoreClient = vsc_module.VectorStoreClient
VectorRecord = vsc_module.VectorRecord
MemoryType = vsc_module.MemoryType


def test_vector_record_creation():
    record = VectorRecord(
        id="test_1",
        vector=[0.1, 0.2, 0.3],
        metadata={"source": "test"},
        namespace="test_ns"
    )
    assert record.id == "test_1"
    assert len(record.vector) == 3
    assert record.metadata["source"] == "test"
    assert record.namespace == "test_ns"


def test_id_generation():
    client = VectorStoreClient(
        api_url="http://localhost",
        api_token="dummy",
    )
    id1 = client._generate_id("P001", 3, MemoryType.CHAT_MESSAGE, "Hello world")
    id2 = client._generate_id("P001", 3, MemoryType.CHAT_MESSAGE, "Hello world")
    assert id1 == id2
    id3 = client._generate_id("P001", 3, MemoryType.CHAT_MESSAGE, "Different")
    assert id1 != id3


def test_client_initialization():
    client = VectorStoreClient(
        api_url="https://api.test.com",
        api_token="test-token",
        account_id="123",
        index_name="test-index",
        dimension=768
    )
    assert client.index_name == "test-index"
    assert client.dimension == 768


@pytest.mark.asyncio
async def test_upsert_single():
    client = VectorStoreClient(
        api_url="http://localhost",
        api_token="dummy",
    )
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"result": {"upserted": 1}}
        vector_id = await client.upsert_single(
            participant_id="P001",
            day_number=1,
            memory_type=MemoryType.DAILY_SUMMARY,
            vector=[0.1, 0.2],
            metadata={"test": True},
            content="Test summary"
        )
        assert vector_id is not None
        assert "P001_1_daily_summary" in vector_id


@pytest.mark.asyncio
async def test_query():
    client = VectorStoreClient(
        api_url="http://localhost",
        api_token="dummy",
    )
    
    mock_matches = [
        {"id": "vec1", "score": 0.95, "metadata": {"type": "chat"}},
        {"id": "vec2", "score": 0.85, "metadata": {"type": "summary"}},
    ]
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"result": {"matches": mock_matches}}
        results = await client.query(
            namespace="test",
            query_vector=[0.1, 0.2],
            top_k=2
        )
        assert len(results) == 2
        assert results[0].id == "vec1"
        assert results[0].score == 0.95


@pytest.mark.asyncio
async def test_query_by_participant():
    client = VectorStoreClient(
        api_url="http://localhost",
        api_token="dummy",
    )
    
    with patch.object(client, 'query', new_callable=AsyncMock) as mock_q:
        mock_q.return_value = []
        await client.query_by_participant(
            participant_id="P001",
            query_vector=[0.1, 0.2],
            memory_type=MemoryType.CHAT_MESSAGE
        )
        mock_q.assert_called_once()
        call_kwargs = mock_q.call_args[1]
        assert mock_q.call_args[0][0] == "participant_P001"
        assert mock_q.call_args[0][3] == {"memory_type": "chat_message"}


@pytest.mark.asyncio
async def test_delete():
    client = VectorStoreClient(
        api_url="http://localhost",
        api_token="dummy",
    )
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"result": {"deleted": 2}}
        result = await client.delete("test_ns", ["id1", "id2"])
        assert result is True
