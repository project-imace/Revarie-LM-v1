"""
vector_retriever.py – RAG Pipeline: Vector Retriever

Semantic search over Cloudflare Vectorize. Retrieves top‑k relevant memories
based on embedding similarity. Supports metadata filtering by participant,
memory type, and day range.

Theoretical Foundations:
- Karpukhin et al. (2020): Dense Passage Retrieval (DPR)
- Lewis et al. (2020): Retrieval‑Augmented Generation
- Johnson et al. (2019): Billion‑scale similarity search with FAISS
"""

import asyncio
import json
import hashlib
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import numpy as np


class MemoryType(Enum):
    CHAT_MESSAGE = "chat_message"
    DAILY_SUMMARY = "daily_summary"
    INFERRED_GOAL = "inferred_goal"
    EMOTIONAL_ANCHOR = "emotional_anchor"
    CONSOLIDATED = "consolidated"


@dataclass
class RetrievalResult:
    """A single retrieved memory fragment."""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    vector: Optional[List[float]] = None


@dataclass
class RetrievalBatch:
    """Batch of retrieval results for a query."""
    query: str
    results: List[RetrievalResult] = field(default_factory=list)
    latency_ms: float = 0.0
    model_used: str = ""


class VectorRetriever:
    """
    Retrieves relevant memories from Cloudflare Vectorize using dense embeddings.
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
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.max_retries = max_retries

        if not self.api_url:
            self.api_url = (
                f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}"
                f"/vectorize/v2/indexes/{self.index_name}"
            )

        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries):
            try:
                session = await self._get_session()
                if method == "POST":
                    async with session.post(url, headers=headers, json=data) as resp:
                        return await self._handle_response(resp)
                elif method == "GET":
                    async with session.get(url, headers=headers) as resp:
                        return await self._handle_response(resp)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError("Max retries exceeded")

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        text = await response.text()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON response: {text[:200]}")
        if response.status >= 400:
            error_msg = data.get("errors", [{}])[0].get("message", "Unknown error")
            raise RuntimeError(f"API error {response.status}: {error_msg}")
        return data

    async def retrieve(
        self,
        namespace: str,
        query_vector: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        include_vectors: bool = False,
    ) -> RetrievalBatch:
        """
        Retrieve nearest neighbors for a query vector.
        """
        import time
        start = time.perf_counter()

        payload = {
            "namespace": namespace,
            "vector": query_vector,
            "topK": top_k,
            "returnValues": include_vectors,
            "returnMetadata": True,
        }
        if filter_metadata:
            payload["filter"] = filter_metadata

        response = await self._request("POST", "/query", payload)
        matches = response.get("result", {}).get("matches", [])

        results = []
        for match in matches:
            results.append(RetrievalResult(
                id=match.get("id", ""),
                content=match.get("metadata", {}).get("content", ""),
                score=match.get("score", 0.0),
                metadata=match.get("metadata", {}),
                vector=match.get("values") if include_vectors else None,
            ))

        latency_ms = (time.perf_counter() - start) * 1000

        return RetrievalBatch(
            query="",
            results=results,
            latency_ms=latency_ms,
            model_used="vectorize",
        )

    async def retrieve_for_participant(
        self,
        participant_id: str,
        query_vector: List[float],
        top_k: int = 5,
        memory_type: Optional[MemoryType] = None,
        day_number: Optional[int] = None,
    ) -> RetrievalBatch:
        """
        Retrieve memories for a specific participant with optional filters.
        """
        namespace = f"participant_{participant_id}"
        filter_metadata = {}

        if memory_type:
            filter_metadata["memory_type"] = memory_type.value
        if day_number is not None:
            filter_metadata["day_number"] = day_number

        return await self.retrieve(
            namespace=namespace,
            query_vector=query_vector,
            top_k=top_k,
            filter_metadata=filter_metadata if filter_metadata else None,
        )
