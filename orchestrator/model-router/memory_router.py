"""
memory_router.py – Model Router: Memory Router

Routes memory recall, summarization, and consolidation tasks to efficient,
high-throughput models. Prioritizes low-latency models for real-time memory
retrieval and larger models for nightly consolidation.

Domain 3: Memory Recall
- Primary:   llama-3.1-8b-instant (Groq) – fastest, low latency
- Secondary: qwen/qwen3-32b (Groq) – higher quality, slightly slower
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MemoryTask(Enum):
    """Type of memory operation."""
    REAL_TIME_RETRIEVAL = "real_time_retrieval"   # During chat, low latency critical
    SUMMARY_GENERATION = "summary_generation"      # Daily consolidation
    EMBEDDING_GENERATION = "embedding_generation"  # Vector creation
    CONSOLIDATION = "consolidation"                # Nightly batch processing


@dataclass
class MemoryRoute:
    """Selected model for a memory task."""
    provider: str
    model: str
    fallback_chain: List[Tuple[str, str]] = field(default_factory=list)
    temperature: float = 0.2
    max_tokens: int = 512
    priority_latency: bool = True


class MemoryRouter:
    """
    Routes memory tasks to appropriate models.
    """

    def __init__(self, key_vault):
        self.key_vault = key_vault

        # Fast models (low latency) for real-time
        self.fast_chain: List[Tuple[str, str]] = [
            ("groq", "llama-3.1-8b-instant"),
        ]

        # Quality models (higher capability) for batch/consolidation
        self.quality_chain: List[Tuple[str, str]] = [
            ("groq", "qwen/qwen3-32b"),
            ("groq", "llama-3.1-8b-instant"),
        ]

        # Task-specific configurations
        self.task_config = {
            MemoryTask.REAL_TIME_RETRIEVAL: {
                "chain": self.fast_chain,
                "temperature": 0.1,
                "max_tokens": 256,
                "priority_latency": True,
            },
            MemoryTask.SUMMARY_GENERATION: {
                "chain": self.quality_chain,
                "temperature": 0.3,
                "max_tokens": 512,
                "priority_latency": False,
            },
            MemoryTask.EMBEDDING_GENERATION: {
                "chain": self.fast_chain,
                "temperature": 0.0,
                "max_tokens": 128,
                "priority_latency": True,
            },
            MemoryTask.CONSOLIDATION: {
                "chain": self.quality_chain,
                "temperature": 0.2,
                "max_tokens": 1024,
                "priority_latency": False,
            },
        }

    def classify_task(self, context: Dict[str, Any]) -> MemoryTask:
        """Classify memory task from context."""
        task_type = context.get("task_type", "real_time_retrieval")

        if task_type == "summary":
            return MemoryTask.SUMMARY_GENERATION
        elif task_type == "embedding":
            return MemoryTask.EMBEDDING_GENERATION
        elif task_type == "consolidation":
            return MemoryTask.CONSOLIDATION
        else:
            return MemoryTask.REAL_TIME_RETRIEVAL

    async def route(self, context: Dict[str, Any]) -> MemoryRoute:
        """Determine optimal model route for a memory task."""
        task = self.classify_task(context)
        config = self.task_config[task]
        chain = config["chain"]

        available_chain = []
        for provider, model in chain:
            key = await self.key_vault.get_key(provider, model)
            if key and key.is_available():
                available_chain.append((provider, model))

        if not available_chain:
            # Fallback to any Groq model
            for provider, model in self.quality_chain + self.fast_chain:
                if provider == "groq":
                    available_chain.append((provider, model))
                    break

        if not available_chain:
            available_chain = [("groq", "llama-3.1-8b-instant")]

        selected = available_chain[0]
        fallback = available_chain[1:3] if len(available_chain) > 1 else []

        return MemoryRoute(
            provider=selected[0],
            model=selected[1],
            fallback_chain=fallback,
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            priority_latency=config["priority_latency"],
        )
