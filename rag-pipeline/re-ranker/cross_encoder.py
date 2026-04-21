"""
cross_encoder.py – RAG Pipeline: Cross‑Encoder Re‑Ranker

Refines retrieval results using a cross‑encoder that jointly encodes
query and document for more accurate relevance scoring.

Theoretical Foundations:
- Nogueira & Cho (2019): Passage Re‑ranking with BERT
- Gao et al. (2021): Reranking for Retrieval‑Augmented Generation
- Thakur et al. (2021): BEIR – Benchmarking Information Retrieval
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import time
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ReRankedResult:
    """A single re‑ranked retrieval result."""
    id: str
    content: str
    original_score: float
    reranked_score: float
    rank_delta: int  # Positive = moved up
    metadata: Dict[str, Any] = field(default_factory=dict)


class CrossEncoderReranker:
    """
    Re‑ranks retrieval results using a cross‑encoder model.
    Supports both local SentenceTransformer cross‑encoders and remote API fallback.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        use_local: bool = True,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        batch_size: int = 32,
    ):
        """
        Initialize the cross‑encoder reranker.

        Args:
            model_name: Hugging Face cross‑encoder model ID
            use_local: Use local sentence‑transformers if available
            api_url: Remote API endpoint for cross‑encoding
            api_key: API key for remote service
            batch_size: Batch size for inference
        """
        self.model_name = model_name
        self.use_local = use_local
        self.api_url = api_url
        self.api_key = api_key
        self.batch_size = batch_size
        self._model = None

        if use_local:
            self._init_local_model()

    def _init_local_model(self):
        """Initialize local cross‑encoder if available."""
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.model_name)
            logger.info(f"Loaded local cross‑encoder: {self.model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed, falling back to heuristics")
            self._model = None
        except Exception as e:
            logger.error(f"Failed to load cross‑encoder: {e}")
            self._model = None

    async def rerank(
        self,
        query: str,
        results: List[Any],
        top_k: int = 5,
    ) -> List[ReRankedResult]:
        """
        Re‑rank a list of retrieval results.

        Args:
            query: Original search query
            results: List of RetrievalResult objects (with id, content, score)
            top_k: Number of results to return after re‑ranking

        Returns:
            Re‑ranked list of results
        """
        if not results:
            return []

        if self._model is not None and self.use_local:
            return self._rerank_local(query, results, top_k)
        elif self.api_url:
            return await self._rerank_remote(query, results, top_k)
        else:
            return self._rerank_heuristic(query, results, top_k)

    def _rerank_local(
        self,
        query: str,
        results: List[Any],
        top_k: int,
    ) -> List[ReRankedResult]:
        """Re‑rank using local cross‑encoder."""
        pairs = [(query, r.content) for r in results]
        scores = self._model.predict(pairs, batch_size=self.batch_size)

        # Normalize scores to 0-1 range
        scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-9)

        reranked = []
        for i, (result, score) in enumerate(zip(results, scores)):
            original_rank = i
            reranked.append(ReRankedResult(
                id=result.id,
                content=result.content,
                original_score=result.score,
                reranked_score=float(score),
                rank_delta=0,  # Will compute after sorting
                metadata=result.metadata,
            ))

        reranked.sort(key=lambda x: x.reranked_score, reverse=True)
        for new_rank, r in enumerate(reranked):
            r.rank_delta = new_rank - original_rank

        return reranked[:top_k]

    async def _rerank_remote(
        self,
        query: str,
        results: List[Any],
        top_k: int,
    ) -> List[ReRankedResult]:
        """Re‑rank using remote API."""
        import aiohttp

        payload = {
            "query": query,
            "documents": [r.content for r in results],
            "model": self.model_name,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, json=payload, headers=headers) as resp:
                data = await resp.json()
                scores = data.get("scores", [])

        # Fallback to heuristic if API fails
        if not scores:
            return self._rerank_heuristic(query, results, top_k)

        reranked = []
        for i, (result, score) in enumerate(zip(results, scores)):
            reranked.append(ReRankedResult(
                id=result.id,
                content=result.content,
                original_score=result.score,
                reranked_score=float(score),
                rank_delta=0,
                metadata=result.metadata,
            ))

        reranked.sort(key=lambda x: x.reranked_score, reverse=True)
        for new_rank, r in enumerate(reranked):
            r.rank_delta = new_rank - i

        return reranked[:top_k]

    def _rerank_heuristic(
        self,
        query: str,
        results: List[Any],
        top_k: int,
    ) -> List[ReRankedResult]:
        """
        Heuristic re‑ranking using query term overlap and recency.
        Fallback when no cross‑encoder is available.
        """
        query_terms = set(query.lower().split())

        reranked = []
        for i, result in enumerate(results):
            content_terms = set(result.content.lower().split())
            overlap = len(query_terms & content_terms)
            overlap_score = min(1.0, overlap / max(len(query_terms), 1))

            # Combine with original score
            combined = 0.6 * result.score + 0.4 * overlap_score

            # Recency boost from metadata
            day_number = result.metadata.get("day_number", 0)
            recency_boost = min(0.1, day_number * 0.01) if day_number else 0.0

            reranked.append(ReRankedResult(
                id=result.id,
                content=result.content,
                original_score=result.score,
                reranked_score=combined + recency_boost,
                rank_delta=0,
                metadata=result.metadata,
            ))

        reranked.sort(key=lambda x: x.reranked_score, reverse=True)
        for new_rank, r in enumerate(reranked):
            r.rank_delta = new_rank - r.rank_delta

        return reranked[:top_k]
