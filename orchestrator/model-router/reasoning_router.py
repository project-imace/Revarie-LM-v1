"""
reasoning_router.py – Model Router: Reasoning Router

Routes complex reasoning tasks to optimal models based on capability,
rate limit availability, and task complexity. Manages fallback chains for
high-availability inference.

Domain 1: Reasoning Models
- Primary:   qwen-3-235b-a22b-instruct-2507 (Cerebras) – best reasoning, watch rate limits
- Secondary: openai/gpt-oss-120b (Groq) – strong fallback, high RPM
- Tertiary:  openai/gpt-oss-20b (Groq) – lightweight fallback
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Classification of reasoning task complexity."""
    SIMPLE = "simple"           # Basic logical inference
    MODERATE = "moderate"       # Multi-step reasoning
    COMPLEX = "complex"         # Deep analytical, counterfactual
    CRITICAL = "critical"       # Requires highest accuracy


@dataclass
class ModelRoute:
    """Selected model for a reasoning task."""
    provider: str
    model: str
    fallback_chain: List[Tuple[str, str]] = field(default_factory=list)
    reasoning_depth: int = 3
    temperature: float = 0.3
    max_tokens: int = 2048


class ReasoningRouter:
    """
    Routes reasoning tasks to optimal models with fallback handling.
    """

    def __init__(self, key_vault):
        """
        Args:
            key_vault: APIKeyVault instance for key management
        """
        self.key_vault = key_vault

        # Model priority chains by complexity
        self.primary_chain: List[Tuple[str, str]] = [
            ("cerebras", "qwen-3-235b-a22b-instruct-2507"),
            ("groq", "openai/gpt-oss-120b"),
            ("groq", "openai/gpt-oss-20b"),
        ]

        self.fallback_only_chain: List[Tuple[str, str]] = [
            ("groq", "openai/gpt-oss-120b"),
            ("groq", "openai/gpt-oss-20b"),
        ]

        # Task complexity → routing configuration
        self.complexity_config = {
            TaskComplexity.SIMPLE: {
                "prefer": [("groq", "openai/gpt-oss-20b")],
                "max_tokens": 1024,
                "temperature": 0.2,
            },
            TaskComplexity.MODERATE: {
                "prefer": [("groq", "openai/gpt-oss-120b")],
                "max_tokens": 2048,
                "temperature": 0.3,
            },
            TaskComplexity.COMPLEX: {
                "prefer": self.primary_chain,
                "max_tokens": 4096,
                "temperature": 0.3,
            },
            TaskComplexity.CRITICAL: {
                "prefer": self.primary_chain,
                "max_tokens": 4096,
                "temperature": 0.1,
            },
        }

        # Rate limit awareness
        self.cerebras_cautious = True  # qwen-235b rate limits easily

    def classify_complexity(self, prompt: str, context: Optional[Dict] = None) -> TaskComplexity:
        """
        Classify the complexity of a reasoning task.
        """
        lower = prompt.lower()
        word_count = len(prompt.split())

        # Critical indicators
        critical_indicators = ["prove", "theorem", "rigorous", "mathematical proof"]
        if any(ind in lower for ind in critical_indicators):
            return TaskComplexity.CRITICAL

        # Complex indicators
        complex_indicators = [
            "analyze", "synthesize", "evaluate", "compare and contrast",
            "why", "how does", "explain the relationship", "multiple factors"
        ]
        if any(ind in lower for ind in complex_indicators) or word_count > 100:
            return TaskComplexity.COMPLEX

        # Moderate indicators
        moderate_indicators = ["explain", "describe", "what are", "summarize"]
        if any(ind in lower for ind in moderate_indicators) or word_count > 50:
            return TaskComplexity.MODERATE

        return TaskComplexity.SIMPLE

    async def route(self, prompt: str, context: Optional[Dict] = None) -> ModelRoute:
        """
        Determine optimal model route for a reasoning task.
        """
        complexity = self.classify_complexity(prompt, context)
        config = self.complexity_config[complexity]
        prefer_chain = config["prefer"]

        # Adjust for Cerebras rate limit sensitivity
        if self.cerebras_cautious and complexity != TaskComplexity.CRITICAL:
            # Skip Cerebras for non-critical tasks if we suspect rate limits
            prefer_chain = [
                (p, m) for (p, m) in prefer_chain
                if p != "cerebras"
            ] or self.fallback_only_chain

        # Build fallback chain
        fallback_chain = []
        selected_provider, selected_model = None, None

        for provider, model in prefer_chain:
            key = await self.key_vault.get_key(provider, model)
            if key and key.is_available():
                if selected_provider is None:
                    selected_provider, selected_model = provider, model
                else:
                    fallback_chain.append((provider, model))

        # If no primary available, use first available from fallback
        if selected_provider is None:
            for provider, model in self.fallback_only_chain:
                key = await self.key_vault.get_key(provider, model)
                if key and key.is_available():
                    selected_provider, selected_model = provider, model
                    break

        # Ultimate fallback
        if selected_provider is None:
            selected_provider, selected_model = "groq", "openai/gpt-oss-20b"

        # Add remaining fallbacks
        for provider, model in self.fallback_only_chain:
            if (provider, model) not in fallback_chain and (provider, model) != (selected_provider, selected_model):
                fallback_chain.append((provider, model))

        # Adjust reasoning depth based on complexity
        depth_map = {
            TaskComplexity.SIMPLE: 1,
            TaskComplexity.MODERATE: 2,
            TaskComplexity.COMPLEX: 4,
            TaskComplexity.CRITICAL: 5,
        }

        return ModelRoute(
            provider=selected_provider,
            model=selected_model,
            fallback_chain=fallback_chain[:3],
            reasoning_depth=depth_map[complexity],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
        )

    def get_stats(self) -> Dict[str, Any]:
        """Return router statistics."""
        return {
            "cerebras_cautious": self.cerebras_cautious,
            "primary_chain": self.primary_chain,
            "complexity_config": {
                k.value: {"prefer": v["prefer"]} for k, v in self.complexity_config.items()
            },
        }
