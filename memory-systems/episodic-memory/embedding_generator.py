"""
embedding_generator.py
Episodic Memory – Embedding Generator.
Generates dense vector embeddings for text input to enable semantic search
and memory consolidation. Supports local Sentence Transformers and remote API
backends with a unified interface.

Theoretical foundations:
- Reimers & Gurevych (2019): Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.
- Retrieval-Augmented Generation (RAG) for memory recall.
"""

import os
import hashlib
import asyncio
import json
from typing import List, Optional, Dict, Any, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
import time


@dataclass
class EmbeddingResult:
    """Result of an embedding generation request."""
    vectors: List[List[float]]
    model_name: str
    dimension: int
    tokens_used: int = 0
    latency_ms: float = 0.0
    cached: bool = False


class EmbeddingBackend(ABC):
    """Abstract base class for embedding generation backends."""

    @abstractmethod
    async def embed(self, texts: List[str]) -> EmbeddingResult:
        """Generate embeddings for a list of texts."""
        pass

    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass

    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier."""
        pass


class LocalSentenceTransformerBackend(EmbeddingBackend):
    """
    Local embedding backend using sentence-transformers.
    Requires: pip install sentence-transformers
    Uses 'all-MiniLM-L6-v2' (384-dim) as default for efficiency.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None
        self._dim = None

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self._model_name)
                self._dim = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise RuntimeError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )

    async def embed(self, texts: List[str]) -> EmbeddingResult:
        self._load_model()
        start = time.perf_counter()
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, lambda: self._model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
        )
        latency = (time.perf_counter() - start) * 1000
        return EmbeddingResult(
            vectors=embeddings.tolist(),
            model_name=self._model_name,
            dimension=self._dim,
            tokens_used=sum(len(t.split()) for t in texts),
            latency_ms=latency,
            cached=False,
        )

    def dimension(self) -> int:
        self._load_model()
        return self._dim

    def model_name(self) -> str:
        return self._model_name


class APIEmbeddingBackend(EmbeddingBackend):
    """
    Remote API embedding backend (e.g., OpenAI, Cohere, Cloudflare Workers AI).
    """

    def __init__(
        self,
        api_url: str,
        api_key: Optional[str] = None,
        model_name: str = "text-embedding-3-small",
        dimension: int = 1536,
        batch_size: int = 100,
        max_retries: int = 3,
    ):
        self.api_url = api_url
        self.api_key = api_key or os.environ.get("EMBEDDING_API_KEY", "")
        self._model_name = model_name
        self._dimension = dimension
        self.batch_size = batch_size
        self.max_retries = max_retries

    async def embed(self, texts: List[str]) -> EmbeddingResult:
        import aiohttp

        all_vectors = []
        tokens_used = 0
        start = time.perf_counter()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                payload = {
                    "model": self._model_name,
                    "input": batch,
                }

                for attempt in range(self.max_retries):
                    try:
                        async with session.post(
                            self.api_url, headers=headers, json=payload
                        ) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                batch_vectors = data.get("data", [])
                                for item in batch_vectors:
                                    all_vectors.append(item.get("embedding", []))
                                tokens_used += data.get("usage", {}).get("total_tokens", 0)
                                break
                            else:
                                if attempt == self.max_retries - 1:
                                    raise RuntimeError(f"API error {resp.status}")
                                await asyncio.sleep(2 ** attempt)
                    except Exception as e:
                        if attempt == self.max_retries - 1:
                            raise
                        await asyncio.sleep(2 ** attempt)

        latency = (time.perf_counter() - start) * 1000
        return EmbeddingResult(
            vectors=all_vectors,
            model_name=self._model_name,
            dimension=self._dimension,
            tokens_used=tokens_used,
            latency_ms=latency,
            cached=False,
        )

    def dimension(self) -> int:
        return self._dimension

    def model_name(self) -> str:
        return self._model_name


class CachedEmbeddingBackend(EmbeddingBackend):
    """
    Wrapper that caches embeddings using a simple in-memory LRU cache.
    """

    def __init__(self, backend: EmbeddingBackend, max_size: int = 10000):
        self.backend = backend
        self.cache: Dict[str, List[float]] = {}
        self.max_size = max_size
        self._access_order: List[str] = []

    def _cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def _evict_if_needed(self):
        while len(self.cache) > self.max_size:
            oldest = self._access_order.pop(0)
            self.cache.pop(oldest, None)

    async def embed(self, texts: List[str]) -> EmbeddingResult:
        uncached_texts = []
        uncached_indices = []
        cached_vectors = [None] * len(texts)
        cache_hits = 0

        for i, text in enumerate(texts):
            key = self._cache_key(text)
            if key in self.cache:
                cached_vectors[i] = self.cache[key]
                cache_hits += 1
                # Move to end (most recently used)
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        if uncached_texts:
            backend_result = await self.backend.embed(uncached_texts)
            for idx, vec in zip(uncached_indices, backend_result.vectors):
                cached_vectors[idx] = vec
                key = self._cache_key(texts[idx])
                self.cache[key] = vec
                self._access_order.append(key)
            self._evict_if_needed()
        else:
            backend_result = EmbeddingResult(
                vectors=[],
                model_name=self.backend.model_name(),
                dimension=self.backend.dimension(),
                tokens_used=0,
                latency_ms=0.0,
                cached=True,
            )

        return EmbeddingResult(
            vectors=cached_vectors,
            model_name=self.backend.model_name(),
            dimension=self.backend.dimension(),
            tokens_used=backend_result.tokens_used,
            latency_ms=backend_result.latency_ms,
            cached=cache_hits == len(texts),
        )

    def dimension(self) -> int:
        return self.backend.dimension()

    def model_name(self) -> str:
        return self.backend.model_name()


class EmbeddingGenerator:
    """
    Main embedding generator with pluggable backends.
    """

    def __init__(self, backend: Optional[EmbeddingBackend] = None):
        if backend is None:
            # Default to local model with cache
            try:
                local = LocalSentenceTransformerBackend()
                backend = CachedEmbeddingBackend(local)
            except RuntimeError:
                # Fallback to mock backend for testing
                backend = MockEmbeddingBackend()
        self.backend = backend

    async def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        result = await self.backend.embed([text])
        return result.vectors[0]

    async def embed_batch(self, texts: List[str]) -> EmbeddingResult:
        """Generate embeddings for a batch of texts."""
        return await self.backend.embed(texts)

    def dimension(self) -> int:
        return self.backend.dimension()

    def model_name(self) -> str:
        return self.backend.model_name()


class MockEmbeddingBackend(EmbeddingBackend):
    """Mock backend for testing (returns random normalized vectors)."""

    def __init__(self, dimension: int = 384):
        self._dimension = dimension

    async def embed(self, texts: List[str]) -> EmbeddingResult:
        import numpy as np
        rng = np.random.default_rng(abs(hash(texts[0])) if texts else 42)
        vectors = []
        for _ in texts:
            vec = rng.normal(size=self._dimension).tolist()
            norm = np.linalg.norm(vec)
            vec = [v / norm for v in vec]
            vectors.append(vec)
        return EmbeddingResult(
            vectors=vectors,
            model_name="mock",
            dimension=self._dimension,
            tokens_used=0,
            latency_ms=0.0,
        )

    def dimension(self) -> int:
        return self._dimension

    def model_name(self) -> str:
        return "mock"


# =============================================================================
# Tests (pytest with asyncio)
# =============================================================================
async def test_mock_backend():
    backend = MockEmbeddingBackend(dimension=128)
    result = await backend.embed(["Hello world", "Test sentence"])
    assert len(result.vectors) == 2
    assert len(result.vectors[0]) == 128
    # Vectors should be normalized
    import numpy as np
    for vec in result.vectors:
        norm = np.linalg.norm(vec)
        assert abs(norm - 1.0) < 0.01


async def test_cached_backend():
    mock = MockEmbeddingBackend(dimension=16)
    cached = CachedEmbeddingBackend(mock, max_size=10)

    # First call should miss cache
    result1 = await cached.embed(["text A", "text B"])
    assert not result1.cached
    assert len(result1.vectors) == 2

    # Second call with same text should hit cache
    result2 = await cached.embed(["text A"])
    assert result2.cached
    assert result2.vectors[0] == result1.vectors[0]

    # Different text misses
    result3 = await cached.embed(["text C"])
    assert not result3.cached


async def test_embedding_generator():
    gen = EmbeddingGenerator(backend=MockEmbeddingBackend(dimension=32))
    vec = await gen.embed_single("Hello")
    assert len(vec) == 32
    batch_result = await gen.embed_batch(["A", "B", "C"])
    assert len(batch_result.vectors) == 3


if __name__ == "__main__":
    async def main():
        gen = EmbeddingGenerator(backend=MockEmbeddingBackend())
        vec = await gen.embed_single("Test")
        print(f"Embedding dim: {len(vec)}, norm: {sum(v*v for v in vec)**0.5:.3f}")

    asyncio.run(main())
