"""
vector_store_client.py
Episodic Memory – Vector Store Client.
Implements a client for Cloudflare Vectorize (or compatible vector database).
Supports storing embeddings, similarity search, and metadata filtering.
Based on Tulving (1972) episodic memory theory.

Theoretical foundations:
- Tulving (1972): Episodic and semantic memory distinction.
- Retrieval-Augmented Generation (RAG) for memory recall.
"""

import os
import json
import hashlib
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
from aiohttp import ClientTimeout, ClientError


class MemoryType(Enum):
    CHAT_MESSAGE = "chat_message"
    DAILY_SUMMARY = "daily_summary"
    INFERRED_GOAL = "inferred_goal"
    EMOTIONAL_ANCHOR = "emotional_anchor"
    CONSOLIDATED = "consolidated"


@dataclass
class VectorRecord:
    """A single vector record stored in the vector database."""
    id: str
    vector: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    namespace: str = "default"
    score: Optional[float] = None  # Set during search


class VectorStoreClient:
    """
    Client for Cloudflare Vectorize API.
    Handles vector upserts, queries, and deletions.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_token: Optional[str] = None,
        account_id: Optional[str] = None,
        index_name: str = "revarie-memory",
        dimension: int = 1536,
        timeout_seconds: int = 30,
        max_retries: int = 3,
    ):
        self.api_url = api_url or os.environ.get("VECTORIZE_API_URL", "")
        self.api_token = api_token or os.environ.get("VECTORIZE_API_TOKEN", "")
        self.account_id = account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
        self.index_name = index_name
        self.dimension = dimension
        self.timeout = ClientTimeout(total=timeout_seconds)
        self.max_retries = max_retries

        if not self.api_url:
            # Construct URL from components
            self.api_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/vectorize/v2/indexes/{self.index_name}"

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        retries: int = 0,
    ) -> Dict[str, Any]:
        """Make authenticated request to Vectorize API with retry logic."""
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        url = f"{self.api_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    if method == "GET":
                        async with session.get(url, headers=headers) as response:
                            return await self._handle_response(response)
                    elif method == "POST":
                        async with session.post(url, headers=headers, json=data) as response:
                            return await self._handle_response(response)
                    elif method == "DELETE":
                        async with session.delete(url, headers=headers) as response:
                            return await self._handle_response(response)
            except (ClientError, asyncio.TimeoutError) as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError("Max retries exceeded")

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Parse and validate API response."""
        text = await response.text()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON response: {text}")

        if response.status >= 400:
            error_msg = data.get("errors", [{}])[0].get("message", "Unknown error")
            raise RuntimeError(f"API error {response.status}: {error_msg}")

        return data

    def _generate_id(
        self,
        participant_id: str,
        day_number: int,
        memory_type: MemoryType,
        content: str,
    ) -> str:
        """Generate a stable, unique vector ID."""
        hash_input = f"{participant_id}_{day_number}_{memory_type.value}_{content}"
        content_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        return f"{participant_id}_{day_number}_{memory_type.value}_{content_hash}"

    async def upsert(
        self,
        namespace: str,
        vectors: List[VectorRecord],
    ) -> bool:
        """
        Insert or update vectors in the index.
        Returns True if successful.
        """
        if not vectors:
            return True

        payload = {
            "namespace": namespace,
            "vectors": [
                {
                    "id": v.id,
                    "values": v.vector,
                    "metadata": v.metadata,
                }
                for v in vectors
            ],
        }

        await self._request("POST", "/upsert", data=payload)
        return True

    async def upsert_single(
        self,
        participant_id: str,
        day_number: int,
        memory_type: MemoryType,
        vector: List[float],
        metadata: Dict[str, Any],
        content: str = "",
    ) -> str:
        """Upsert a single vector and return its generated ID."""
        vector_id = self._generate_id(participant_id, day_number, memory_type, content)
        record = VectorRecord(
            id=vector_id,
            vector=vector,
            metadata={
                **metadata,
                "participant_id": participant_id,
                "day_number": day_number,
                "memory_type": memory_type.value,
            },
            namespace=f"participant_{participant_id}",
        )
        await self.upsert(record.namespace, [record])
        return vector_id

    async def query(
        self,
        namespace: str,
        query_vector: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        include_values: bool = False,
        include_metadata: bool = True,
    ) -> List[VectorRecord]:
        """
        Query the vector index for nearest neighbors.
        Returns list of VectorRecord sorted by similarity (highest first).
        """
        payload = {
            "namespace": namespace,
            "vector": query_vector,
            "topK": top_k,
            "returnValues": include_values,
            "returnMetadata": include_metadata,
        }

        if filter_metadata:
            payload["filter"] = filter_metadata

        response = await self._request("POST", "/query", data=payload)

        matches = response.get("result", {}).get("matches", [])
        records = []
        for match in matches:
            records.append(
                VectorRecord(
                    id=match.get("id", ""),
                    vector=match.get("values", []) if include_values else [],
                    metadata=match.get("metadata", {}),
                    namespace=namespace,
                    score=match.get("score", 0.0),
                )
            )
        return records

    async def query_by_participant(
        self,
        participant_id: str,
        query_vector: List[float],
        top_k: int = 5,
        memory_type: Optional[MemoryType] = None,
    ) -> List[VectorRecord]:
        """
        Query vectors for a specific participant, optionally filtered by memory type.
        """
        namespace = f"participant_{participant_id}"
        filter_metadata = None
        if memory_type:
            filter_metadata = {"memory_type": memory_type.value}

        return await self.query(namespace, query_vector, top_k, filter_metadata)

    async def delete(
        self,
        namespace: str,
        vector_ids: List[str],
    ) -> bool:
        """
        Delete vectors by ID.
        """
        if not vector_ids:
            return True

        payload = {
            "namespace": namespace,
            "ids": vector_ids,
        }
        await self._request("POST", "/delete", data=payload)
        return True

    async def delete_by_metadata(
        self,
        namespace: str,
        filter_metadata: Dict[str, Any],
    ) -> int:
        """
        Delete vectors matching metadata filter.
        Returns number of vectors deleted (estimated).
        """
        payload = {
            "namespace": namespace,
            "filter": filter_metadata,
        }
        response = await self._request("POST", "/delete-by-metadata", data=payload)
        return response.get("result", {}).get("count", 0)

    async def get_by_id(
        self,
        namespace: str,
        vector_id: str,
    ) -> Optional[VectorRecord]:
        """
        Fetch a single vector by ID.
        """
        payload = {
            "namespace": namespace,
            "ids": [vector_id],
        }
        response = await self._request("POST", "/fetch", data=payload)
        vectors = response.get("result", {}).get("vectors", [])
        if vectors:
            v = vectors[0]
            return VectorRecord(
                id=v.get("id", ""),
                vector=v.get("values", []),
                metadata=v.get("metadata", {}),
                namespace=namespace,
            )
        return None

    async def describe_index(self) -> Dict[str, Any]:
        """Get index statistics and configuration."""
        response = await self._request("GET", "/describe")
        return response.get("result", {})


# =============================================================================
# Tests (pytest with asyncio)
# =============================================================================
async def test_vector_record_creation():
    record = VectorRecord(
        id="test_1",
        vector=[0.1, 0.2, 0.3],
        metadata={"source": "test"},
    )
    assert record.id == "test_1"
    assert len(record.vector) == 3


async def test_id_generation():
    client = VectorStoreClient(
        api_url="http://localhost",
        api_token="dummy",
    )
    id1 = client._generate_id("P001", 3, MemoryType.CHAT_MESSAGE, "Hello world")
    id2 = client._generate_id("P001", 3, MemoryType.CHAT_MESSAGE, "Hello world")
    assert id1 == id2  # Stable
    id3 = client._generate_id("P001", 3, MemoryType.CHAT_MESSAGE, "Different")
    assert id1 != id3


# Mock tests for CI (no real API calls)
class MockResponse:
    def __init__(self, status, data):
        self.status = status
        self._data = data

    async def text(self):
        return json.dumps(self._data)

    async def json(self):
        return self._data


async def test_client_initialization():
    client = VectorStoreClient(
        api_url="https://api.cloudflare.com/client/v4/accounts/123/vectorize/v2/indexes/test",
        api_token="test-token",
    )
    assert client.index_name == "test"
    assert client.dimension == 1536


if __name__ == "__main__":
    # Simple sync test for manual validation
    client = VectorStoreClient(
        api_url="http://localhost:8787",
        api_token="dummy",
    )
    test_id = client._generate_id("P001", 1, MemoryType.DAILY_SUMMARY, "Test summary")
    print(f"Generated ID: {test_id}")
