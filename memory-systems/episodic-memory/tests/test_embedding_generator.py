"""
test_embedding_generator.py
Unit tests for Embedding Generator.
"""

import sys
import os
import importlib.util
import asyncio

import pytest

# Dynamically load the module
module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "embedding_generator.py")
)
spec = importlib.util.spec_from_file_location("embedding_generator", module_path)
eg_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eg_module)

EmbeddingGenerator = eg_module.EmbeddingGenerator
MockEmbeddingBackend = eg_module.MockEmbeddingBackend
CachedEmbeddingBackend = eg_module.CachedEmbeddingBackend
EmbeddingResult = eg_module.EmbeddingResult


@pytest.mark.asyncio
async def test_mock_backend_dimension():
    backend = MockEmbeddingBackend(dimension=128)
    result = await backend.embed(["Hello world"])
    assert len(result.vectors[0]) == 128
    assert result.model_name == "mock"
    assert result.dimension == 128


@pytest.mark.asyncio
async def test_mock_backend_normalized():
    backend = MockEmbeddingBackend(dimension=16)
    result = await backend.embed(["Test"])
    import numpy as np
    vec = result.vectors[0]
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 0.01


@pytest.mark.asyncio
async def test_cached_backend_hit():
    mock = MockEmbeddingBackend(dimension=16)
    cached = CachedEmbeddingBackend(mock, max_size=10)
    
    result1 = await cached.embed(["text A", "text B"])
    assert not result1.cached
    assert len(result1.vectors) == 2
    
    result2 = await cached.embed(["text A"])
    assert result2.cached
    assert result2.vectors[0] == result1.vectors[0]
    
    result3 = await cached.embed(["text C"])
    assert not result3.cached


@pytest.mark.asyncio
async def test_cached_backend_eviction():
    mock = MockEmbeddingBackend(dimension=16)
    cached = CachedEmbeddingBackend(mock, max_size=2)
    
    await cached.embed(["A"])
    await cached.embed(["B"])
    await cached.embed(["C"])
    # A should be evicted
    result = await cached.embed(["A"])
    assert not result.cached


@pytest.mark.asyncio
async def test_embedding_generator_single():
    gen = EmbeddingGenerator(backend=MockEmbeddingBackend(dimension=32))
    vec = await gen.embed_single("Hello")
    assert len(vec) == 32


@pytest.mark.asyncio
async def test_embedding_generator_batch():
    gen = EmbeddingGenerator(backend=MockEmbeddingBackend(dimension=32))
    result = await gen.embed_batch(["A", "B", "C"])
    assert len(result.vectors) == 3
    assert result.dimension == 32


def test_embedding_result_properties():
    result = EmbeddingResult(
        vectors=[[0.1, 0.2]],
        model_name="test",
        dimension=2,
        tokens_used=5,
        latency_ms=10.5,
        cached=True
    )
    assert result.model_name == "test"
    assert result.tokens_used == 5
    assert result.latency_ms == 10.5
    assert result.cached is True
